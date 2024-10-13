import streamlit as st
import json
from twelvelabs import TwelveLabs
from twelvelabs.models.task import Task

class VideoAnalysis:
    def __init__(self):
        self.api_key = "tlk_14G0MC31C66JK62SNTX2K1MAX2AR"
        # self.index_name = index_name
        self.client = TwelveLabs(api_key=self.api_key)
        self.index_id = "670b4810eaac6725641d655f"
        self.video_ids = ["670bd5cd9da39d4c05a1efaa"]  # List to store video IDs
        self.video_id_new = ""

    def create_index(self):
        try:
            index = self.client.index.create(
                name=self.index_name,
                engines=[
                    {
                        "name": "pegasus1.1",
                        "options": ["visual", "conversation"],
                    }
                ]
            )
            self.index_id = index.id
            st.success(f"Created index: id={self.index_id}")
        except Exception as e:
            st.error(f"Index already exists or error occurred: {e}")

    def upload_video(self, video_path):
        if not self.index_id:
            st.error("Index ID not found. Create or load an index first.")
            return

        try:
            task = self.client.task.create(
                index_id=self.index_id,
                file=video_path,
                language="en"  # Assuming English video, can modify for other languages
            )
            st.info(f"Uploading video... Task id={task.id}")
            self.monitor_task(task)
        except Exception as e:
            st.error(f"Error occurred while uploading video: {e}")

    def monitor_task(self, task):
        def on_task_update(task: Task):
            st.info(f"Status={task.status}")

        task.wait_for_done(sleep_interval=50, callback=on_task_update)
        if task.status != "ready":
            st.error(f"Indexing failed with status {task.status}")
        else:
            self.video_id_new = task.video_id
            st.success(f"Video uploaded successfully. Video ID={task.video_id}")
            self.video_ids.append(str(task.video_id))

    def list_videos(self):
        if not self.index_id:
            st.error("Index ID not found. Create or load an index first.")
            return

        try:
            videos = self.client.index.video.list(self.index_id)
            for video in videos:
                self.video_ids.append(video.id)
                st.info(f"Video ID: {video.id}")

            if not self.video_ids:
                st.info("No videos found in the index.")
            else:
                st.info(f"Total videos found: {len(self.video_ids)}")
        except Exception as e:
            st.error(f"Error occurred while listing videos: {e}")

    def generate_safety_report(self, video_id):
        prompt = """Analyze the following video and classify its content based on explicit or restricted materials. Return the output in the following JSON format: {"safe": "Yes" or "No", "explicit_content": { "Explicit Nudity": [Yes/No, Severity], "Sexual Content": [Y/N, Severity], "Violence": [Y/N, Severity], "Hate Speech": [Y/N, Severity], "Drug Use": [Y/N, Severity], "Alcohol Use": [Y/N, Severity], "Smoking": [Y/N, Severity], "Profanity": [Y/N, Severity], "Gambling": [Y/N, Severity], "Self-harm/Suicide": [Y/N, Severity], "Animal Cruelty": [Y/N, Severity], "Terrorism/Extremism": [Y/N, Severity], "Disturbing/Graphic Imagery": [Y/N, Severity], "Child Endangerment": [Y/N, Severity], "Weapons": [Y/N, Severity], "Mature Themes": [Y/N, Severity],
                "Suggestive Content": [Y/N, Severity],
                "Dangerous Acts": [Y/N, Severity],
                "Misleading Information": [Y/N, Severity],
            },
            "annotations": {
                "explicit content": ["exact timestamp of the video where the explicit content is found"]
            }
        }
        explicit content - [yes/no, severity - high, medium, low, None] Analyze the video carefully and ensure all relevant content types are marked appropriately. If the video is safe, mark the "safe" field as "Yes"; otherwise, mark it as "No" and provide the specific categories where explicit content is present."""
        try:
            res = self.client.generate.text(
                video_id=video_id,
                prompt=prompt
            )
            # st.success(f"Safety report for video {video_id}: {res.data}")
            return res.data
        
        except Exception as e:
            st.error(f"Error generating safety report: {e}")
            return None

class VideoComplianceChecker:
    def __init__(self):
         self.country_regulations = {
            "USA": {
                "Explicit Nudity": ("No", None),
                "Sexual Content": ("No", None),
                "Violence": ("No", None),
                "Hate Speech": ("No", None),
                "Drug Use": ("Yes", "Low"),
                "Alcohol Use": ("Yes", "Low"),
                "Smoking": ("Yes", "Low"),
                "Profanity": ("Yes", "Low"),
                "Gambling": ("Yes", None),
                "Self-harm/Suicide": ("Yes", "Low"),
                "Animal Cruelty": ("Yes", None),
                "Terrorism/Extremism": ("Yes", None),
                "Disturbing/Graphic Imagery": ("Yes", None),
                "Child Endangerment": ("Yes", None),
                "Weapons": ("Yes", None),
                "Mature Themes": ("Yes", "Low"),
                "Suggestive Content": ("Yes", None),
                "Dangerous Acts": ("Yes", None),
                "Misleading Information": ("Yes", None),
                "Unclear/Obscured Content": ("Yes", None)
            },
            "China": {
                "Explicit Nudity": ("No", None),
                "Sexual Content": ("No", None),
                "Violence": ("No", None),
                "Hate Speech": ("No", None),
                "Drug Use": ("No", None),
                "Alcohol Use": ("No", None),
                "Smoking": ("Yes", "Low"),
                "Profanity": ("No", None),
                "Gambling": ("No", None),
                "Self-harm/Suicide": ("No", None),
                "Animal Cruelty": ("No", None),
                "Terrorism/Extremism": ("No", None),
                "Disturbing/Graphic Imagery": ("No", None),
                "Child Endangerment": ("No", None),
                "Weapons": ("No", None),
                "Mature Themes": ("No", None),
                "Suggestive Content": ("No", None),
                "Dangerous Acts": ("No", None),
                "Misleading Information": ("No", None),
                "Unclear/Obscured Content": ("No", None)
            },
            "India": {
                "Explicit Nudity": ("No", None),
                "Sexual Content": ("No", None),
                "Violence": ("No", None),
                "Hate Speech": ("No", None),
                "Drug Use": ("No", None),
                "Alcohol Use": ("Yes", "Low"),
                "Smoking": ("Yes", "High"),
                "Profanity": ("Yes", "Low"),
                "Gambling": ("No", None),
                "Self-harm/Suicide": ("No", None),
                "Animal Cruelty": ("No", None),
                "Terrorism/Extremism": ("No", None),
                "Disturbing/Graphic Imagery": ("No", None),
                "Child Endangerment": ("No", None),
                "Weapons": ("No", None),
                "Mature Themes": ("Yes", "Low"),
                "Suggestive Content": ("No", None),
                "Dangerous Acts": ("No", None),
                "Misleading Information": ("No", None),
                "Unclear/Obscured Content": ("No", None)
            }
        }

    def check_compliance(self, video_data):
        compliance_result = {}
        all_safe = True

        for country, regulations in self.country_regulations.items():
            violations = []
            for content_type, (allowed_presence, allowed_severity) in regulations.items():
                if content_type in video_data['explicit_content']:
                    presence, severity = video_data['explicit_content'][content_type]
                    if presence == "Yes" and allowed_presence == "No":
                        violations.append(content_type)
                    elif allowed_severity and severity != "None" and severity != allowed_severity:
                        violations.append(content_type)

            if violations:
                all_safe = False
                compliance_result[country] = violations
            else:
                compliance_result[country] = "Safe"

        if all_safe:
            return "Video is safe"
        else:
            return compliance_result

# Streamlit App Code

st.title("Video Content Regulation Checker")

# api_key = st.text_input("Enter API Key", type="password")
# index_name = st.text_input("Enter Index Name")

# if api_key and index_name:
video_analysis = VideoAnalysis()
st.info("Video analysis initialized.")

# Add a button to create the index
if st.button("Create Index"):
    video_analysis.create_index()
    if video_analysis.index_id:
        st.info(f"Index created successfully. ID: {video_analysis.index_id}")

video_file = st.file_uploader("Upload a Video", type=["mp4", "mov", "avi"])

if st.button("Upload and Index Video") and video_file:
    video_analysis.upload_video(video_file)

if st.button("Generate Safety Report"):

    video_id = video_analysis.video_ids[-1]
    # st.write(video_id)
    video_data = video_analysis.generate_safety_report(video_analysis.video_id_new)
    # st.write(video_data)

    if video_data:
        # Process and display the compliance result
        compliance_checker = VideoComplianceChecker()
        video_data = video_data[video_data.find('{'): len(video_data) - video_data[::-1].find("}")]
        # st.write(video_data)
        parsed_json = json.loads(video_data)
        pretty_json = json.dumps(parsed_json, indent=4)
        
        # Display the pretty-printed JSON string as code in Streamlit
        st.code(pretty_json, language="json")
        video_data = json.loads(video_data)
        result = compliance_checker.check_compliance(video_data)
        st.write(result)
    else:
        st.error("No video uploaded. Please upload a video first.")
