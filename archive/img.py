import os
import re
import shutil

def main():
    images_dir = os.path.join(os.getcwd(), "images")
    os.makedirs(images_dir, exist_ok=True)

    pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')

    def is_remote_or_nonfile(path: str) -> bool:
        path = path.lower().strip()
        return path.startswith(("http://", "https://", "data:", "file://"))

    for md_file in [f for f in os.listdir('.') if f.endswith('.md')]:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = content

        for match in pattern.finditer(content):
            alt_text, old_path = match.groups()
            if is_remote_or_nonfile(old_path):
                continue

            old_path = old_path.strip().replace('\\', '/').strip('<>') # remove surrounding <> in file paths with spaces
            old_filename = os.path.basename(old_path)
            file_ext = os.path.splitext(old_filename)[1]

            if not file_ext: # or file_ext.lower() not in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp"]:
                continue

            safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', alt_text).strip().replace(' ', '_')
            if not safe_name:
                safe_name = "image"

            new_filename = f"{safe_name}{file_ext}"
            new_path = os.path.join(images_dir, new_filename)

            # Detect the actual source
            if os.path.exists(old_path):
                source_path = old_path
            elif os.path.exists(old_filename):
                source_path = old_filename
            elif os.path.exists(os.path.join(images_dir, old_filename)):
                source_path = os.path.join(images_dir, old_filename)
            else:
                print(f"⚠️ Warning: {old_path} not found")
                continue

            # If the source is already the correct file in images, skip move
            if os.path.abspath(source_path) != os.path.abspath(new_path):
                counter = 1
                original_new_path = new_path
                while os.path.exists(new_path):
                    if os.path.abspath(new_path) == os.path.abspath(source_path):
                        # already correct
                        break
                    new_filename = f"{safe_name}_{counter}{file_ext}"
                    new_path = os.path.join(images_dir, new_filename)
                    counter += 1

                if os.path.abspath(source_path) != os.path.abspath(new_path):
                    shutil.move(source_path, new_path)
                    # print(f"Moved: {source_path} → {new_path}")
            # else:
                # print(f"✅ Already up-to-date: {new_path}")

            # Only update Markdown if path changed
            new_relative_path = os.path.join("images", new_filename)
            new_markdown = f"![{alt_text}]({new_relative_path})"
            # new_markdown = f"![{alt_text}]({new_path})"
            new_content = new_content.replace(match.group(0), new_markdown)

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

    print("\n✅ All Markdown files processed safely.")

if __name__ == "__main__":
    main()
