import os
import re
import shutil
from pathlib import Path

# Track processed media: {source_abs_path: {"filename": new_filename, "name": title/alt, "moved": bool, "duplicate": bool}}
processed_files = {}

# Track stats for summary
stats = {
    "total_files": 0,
    "moved": 0,
    "duplicates": 0,
    "skipped": 0
}

def main():
    media_dir = Path.cwd() / "media"
    media_dir.mkdir(exist_ok=True)

    md_files = [f for f in os.listdir('.') if f.endswith('.md')]

    # Regex patterns
    md_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
    html_media_pattern = re.compile(r'<(audio|video)([^>]*)src=["\'](.*?)["\']([^>]*)>', re.IGNORECASE)

    for md_file in md_files:
        md_path = Path(md_file)
        content = md_path.read_text(encoding='utf-8')

        # Replace Markdown image references
        content = md_pattern.sub(lambda m: process_file_reference(
            old_path=m.group(2),
            name_for_file=m.group(1),
            match=m,
            media_dir=media_dir,
            prefix="image",
            html_tag=False
        ), content)

        # Replace HTML audio/video references
        content = html_media_pattern.sub(lambda m: process_file_reference(
            old_path=m.group(3),
            name_for_file=(re.search(r'title=["\'](.*?)["\']', m.group(2)+m.group(4), re.IGNORECASE).group(1)
                           if re.search(r'title=["\'](.*?)["\']', m.group(2)+m.group(4), re.IGNORECASE) else Path(m.group(3)).stem),
            match=m,
            media_dir=media_dir,
            prefix=m.group(1).lower(),
            html_tag=True
        ), content)

        md_path.write_text(content, encoding='utf-8')

    # Second pass: propagate changes to all files for duplicate occurrences
    propagate_changes(md_files)

    print(r"""
          

                  @@@@@@                                                     
              @@@       @                                                    
           @@@        .@                                                     
          @#        @@@                                                      
        @@   -@@@@@@                                                         
       @  @@@   @@  @@*.=@@@@@@@                                             
      @  @@     @+             @                                             
     @@ @@      @@            @@                                             
     @% @       @        ==    @                                             
     @@ @       @  #    @-*    @                                             
      @  @@      @@=    @*#  @@                                              
       @  .@@     @@    +@@@ @@                                              
        @@    *@@@@@@@#@:     =@@@@@@                                        
           @@@       =     @ @  @      @@@                                   
                @@@@@@ @   @ @   @@@@@*   *@                                 
                     @       #   =@     @@  @@                               
                     @ @     * : =@       @  @                               
                     @- @@+  %@  @@@      @@ @                               
                       @@ =@@@@ @.   @@@@@: -@                               
                      @@  =@ @  @@@@@      @@                                
                      @   @@ @  @@    @@@@                                   
                     @%   @ @@  @@                                           
                      @ @@  @@  @@                                           
                             @@@@                                            
                                                                             
                                                    
    """)

    # Summary report
    print("\n✅ All Markdown files processed safely.\n")
    print("📊 Summary Report:")
    print(f"Total media references processed: {stats['total_files']}")
    print(f"Files moved to media folder: {stats['moved']}")
    print(f"Duplicates renamed: {stats['duplicates']}")
    print(f"References skipped (file not found): {stats['skipped']}")


def process_file_reference(old_path, name_for_file, match, media_dir, prefix, html_tag=False):
    stats['total_files'] += 1
    old_path = Path(old_path.strip().replace('\\','/').strip('<>'))
    source_path = None

    # Locate the source file
    possible_paths = [
        old_path,
        Path.cwd() / old_path.name,
        media_dir / old_path.name
    ]
    for p in possible_paths:
        if p.exists():
            source_path = p.resolve()
            break

    if not source_path:
        print(f"⚠️ Warning: {old_path} not found")
        stats['skipped'] += 1
        return match.group(0)

    # Sanitize name
    safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', name_for_file).strip().replace(' ', '_')
    if not safe_name:
        safe_name = prefix

    ext = source_path.suffix
    new_filename = f"{safe_name}{ext}"
    new_path = media_dir / new_filename

    duplicate = False
    # Handle duplicates
    counter = 1
    while new_path.exists() and new_path.resolve() != source_path:
        new_filename = f"{safe_name}_{counter}{ext}"
        new_path = media_dir / new_filename
        counter += 1
        duplicate = True

    # Move file if needed
    moved = False
    if source_path.resolve() != new_path.resolve():
        shutil.move(str(source_path), str(new_path))
        moved = True

    # Always update processed_files with the latest filename
    processed_files[str(source_path)] = {
        "filename": new_filename,
        "name": name_for_file,
        "moved": moved,
        "duplicate": duplicate
    }

    if moved:
        stats['moved'] += 1
    if duplicate:
        stats['duplicates'] += 1

    new_relative_path = f"media/{new_filename}"

    # Return replacement tag
    if html_tag:
        old_tag = match.group(0)
        new_tag = re.sub(r'src=["\'](.*?)["\']', f'src="{new_relative_path}"', old_tag)
        if re.search(r'title=["\'].*?["\']', new_tag, re.IGNORECASE):
            new_tag = re.sub(r'title=["\'].*?["\']', f'title="{name_for_file}"', new_tag)
        else:
            new_tag = new_tag.replace('>', f' title="{name_for_file}">')
        return new_tag
    else:
        return f'![{name_for_file}]({new_relative_path})'


def propagate_changes(md_files):
    for md_file in md_files:
        md_path = Path(md_file)
        content = md_path.read_text(encoding='utf-8')
        updated_content = content

        for source_path, info in processed_files.items():
            old_filename = re.escape(Path(source_path).name)
            new_filename = info["filename"]
            new_name = info["name"]

            # Markdown images (absolute, relative, with or without < >)
            updated_content = re.sub(
                rf'!\[.*?\]\(<?(?:media/|.*[/\\])?{old_filename}>?\)',
                f'![{new_name}](media/{new_filename})',
                updated_content
            )

            # HTML audio/video
            updated_content = re.sub(
                rf'<(audio|video)([^>]*)src=["\'](?:media/|.*[/\\])?{old_filename}["\']([^>]*)>',
                lambda m: update_html_tag(m, new_filename, new_name),
                updated_content,
                flags=re.IGNORECASE
            )

        md_path.write_text(updated_content, encoding='utf-8')


def update_html_tag(match, new_filename, new_title):
    tag = match.group(1)
    before = match.group(2)
    after = match.group(3)
    new_tag = f'<{tag}{before}src="media/{new_filename}"{after}>'
    if re.search(r'title=["\'].*?["\']', new_tag, re.IGNORECASE):
        new_tag = re.sub(r'title=["\'].*?["\']', f'title="{new_title}"', new_tag)
    else:
        new_tag = new_tag.replace('>', f' title="{new_title}">')
    return new_tag


if __name__ == "__main__":
    main()
