# import base64
# from datetime import datetime
# import os
# import json
# from openai import OpenAI
# from streamlit import json

import os
import base64
import json
from datetime import datetime
from openai import OpenAI


client = OpenAI(api_key="")

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_cluster_json(image_path):
    base64_image = encode_image(image_path)

    prompt = """
                You are an expert in architectural floorplan understanding.

                Given a floorplan image, extract a structured cluster graph.

                Your task:
                1. Identify all spaces:
                - rooms inside flats (bedroom, kitchen, living_room, bathroom, dining, etc.)
                - common areas (lobby, corridor, staircase, lift)

                2. Group rooms into individual housing units (e.g., 1BHK, 2BHK, etc.)

                3. Assign unique names:
                - bedroom_1_u1, bedroom_2_u1, etc.
                - living_room_u1, kitchen_u2, etc.
                - entrance_u1, entrance_u2
                - common areas: lobby, corridor, staircase, lift_1, lift_2

                4. Identify connections:
                - If two spaces are directly connected via a door, create a relationship

                5. Output ONLY valid JSON in this format:

                {
                "relationships": [
                    {
                    "room1": "string",
                    "room2": "string",
                    "has_door": true
                    }
                ]
                }

                Rules:
                - Do NOT invent rooms not visible
                - Ensure the graph is connected
                - Use consistent naming
                - Each unit must connect to corridor or lobby via entrance
                - No explanations, only JSON
            """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


# if __name__ == "__main__":
#     image_path = "shubarambh_mumbai.png"  # change this
#     output = generate_cluster_json(image_path)
#     print("\nGenerated JSON:\n")
#     print(output)


# ---------- Validate JSON ----------

def clean_json_output(text):
    # remove markdown ```json ... ```
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def validate_json(output_text):
    try:
        cleaned = clean_json_output(output_text)
        return json.loads(cleaned)
    except Exception as e:
        print("JSON parsing failed:", e)
        return None


# def validate_json(output_text):
#     try:
#         return json.loads(output_text)
#     except Exception as e:
#         print("JSON parsing failed:", e)
#         return None


# ---------- Save JSON ----------
def save_json(data, output_dir="outputs", filename=None):
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cluster_shubarambh_{timestamp}.json"

    file_path = os.path.join(output_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f" JSON saved at: {file_path}")
    return file_path


# ---------- Main ----------
if __name__ == "__main__":
    image_path = "shubarambh_mumbai.png"  # change this
    print("Processing image...")
    raw_output = generate_cluster_json(image_path)
    print("\nRaw Model Output:\n")
    print(raw_output)
    parsed_json = validate_json(raw_output)

    if parsed_json:
        save_json(parsed_json)
    else:
        print("Skipping save due to invalid JSON")