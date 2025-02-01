def read_story_file_to_dict(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.readlines()

    output_dict = {}
    key = "None"
    for line in data:
        if line.startswith("[["):
            key = line.strip().replace("[[", "").replace("]]", "")
            output_dict[key] = ""
        else:
            output_dict[key] += (line.strip() + "\n")

    return output_dict
