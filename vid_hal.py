
import os
os.environ['TWELVELABS_API_KEY'] = 'tlk_14G0MC31C66JK62SNTX2K1MAX2AR'
os.environ['HALLUCINATION_API_KEY'] = 'e6746d7-fcb2-4bda-8f08-f489a3d95ec1-fa56966810a02357'
# Set your API keys as environment variables

import streamlit as st
import requests
import os
import json

# Set your API keys as environment variables or hardcode them (not recommended for production)
TWELVELABS_API_KEY = os.environ.get('TWELVELABS_API_KEY') or 'your_twelvelabs_api_key'
HALLUCINATION_API_KEY = os.environ.get('HALLUCINATION_API_KEY') or 'your_hallucination_api_key'

# API configuration
TWELVELABS_BASE_URL = 'https://api.twelvelabs.io/v1.2'
HALLUCINATION_API_URL = "https://llm.kindo.ai/v1/chat/completions"
MODEL_NAME = "azure/gpt-4o"

# Specify the index ID here
INDEX_ID = "670b6e39e2f5d6a324a6ba2b"  # Replace with your actual index ID

# Check for API keys
if not TWELVELABS_API_KEY or not HALLUCINATION_API_KEY:
    st.error("Please set your TwelveLabs and Hallucination API keys in the environment variables.")
    st.stop()

# Dictionary mapping video IDs to local file paths
video_id_to_filepath = {
    '670b72b89da39d4c05a1eee6': 'transcript_videos/Own the Moon and Mars.mp4',
    '670b72b8c0f5f53791d8ea52': 'transcript_videos/Buffalo Chicken Sliders.mp4',
    '670b72b8c0f5f53791d8ea53': 'transcript_videos/Cooking Chicken Particle Accelerator.mp4',
    '670b72b59da39d4c05a1eee5': "transcript_videos/Why Can't Robots Check I'm Not A Robot.mp4",
    # Add more mappings as needed
}

# Hardcoded transcripts mapping
transcripts = {
    '670b72b89da39d4c05a1eee6': """you own the moon and Mars and everything
else in space really call a space lawyer
they'll tell you about the outer space
treaty it was born from the Cold War
when countries were racing to space it
forbids any of them from taking over
celestial bodies stuff in space is a
common good open to everyone unlike the
oceans and skies benefits us all but
what if you build a rocket land on the
moon and pick up a rock is it your rock
now if you bring it back to Earth can it
become your private property it depends
on who you ask the US and many others
are following new rules the emis Accords
they were designed to make room for
space mining you even get a safety zone
around your Landing site so no one can
disturb your work but what if you land
on a spot someone else wants what if
your Rockets completely cover an
asteroid it's still unclear what happens
then Russia and China have not signed
the Accords there's no clear way to
resolve disputes between everyone so
you'd better pay those lawyers fees and
get some good space Insurance you may
lose your rocks but at least""",
    '670b72b8c0f5f53791d8ea52': """all right y'all we about to make some
chicken bacon ranch sliders for the
football game baby let's go all right
y'all one stick of butter babe now cut
them chicken thighs thin y'all onion
powder salt and pepper baby now go up on
your griddle put your chicken and some
buffalo sauce go ahead on and get that
bacon on now that chicken and that
Bacon's cooking up let's make some ranch
sauce 2 tbsp mayonnaise 3 tbsp sour
cream go at the fresh dill fresh parsley
garlic powder salt and pepper butter
milk to your consistency put it on and
give it a good mix now go up on it with
the Hawaiian rolls mozzarella cheese now
your chicken layer it up with your bacon
put some of that ranch on there now put
the top on there go ahead on with that
butter right on top and that ranch
seasoning all right y'all I dip it off
in that ranch we made""",
    '670b72b8c0f5f53791d8ea53': """cooking a chicken with a particle
accelerator how would that work first we
need a raw chicken that's easy then we
need a particle accelerator so let's put
a chicken in it to avoid collisions
between air molecules and beam particles
we have to pump out all the air in the
beam pipe before we even turn it on as
the air pressure drops to near vacuum
moisture and other molecules vaporize
leaving the outer layer of the chicken
dried and brittle then as we cool down
the magnet any water remaining freezes
when the beam is turned on magnetic
fields focus it to the width of a hair
so it only collides with a narrow strand
of chicken but it completely obliterates
every atom in its way the tremendous
energy of the collisions burns the meat
around it or it would if there were any
Oxygen for it to burn and the space
around this hole doesn't stay raw rather
it becomes radioactive when we finally
pull our chicken out of the accelerator
it's not exactly raw but it's certainly
not cooked you can take a bite once it
thaws but we're not fans of food
poisoning or radiation poisoning so we
can't
recommend""",
    '670b72b59da39d4c05a1eee5': """I have a question: why can't a robot just click
I'm not a robot?turns out that the answer to
that question is part of a bigger story about
being human. the tech is called reCAPTCHA. it
stands for "completely automated public turing
test to tell computers and humans apart." you
might remember some of these older versions or
these. robots are pretty good at those ones now
but the box test isn't really about the box. it's
tracking all kinds of other things about your
behavior like for example where you put the mouse
before you click the box. robots move like this
but humans move kind of like this. in other words
these aren't about what makes humans better than
robots. they're about what makes humans human.
that's not new. it's the same question we've been
thinking about for centuries and in a world where
technology can do more and more surprising things,
I think there's something kind of beautiful about
constantly trying to figure out what makes us
differentiated human. if you like optimistic
science and tech stories follow for more...""",
    # Add more video IDs and their transcripts as needed
}

def get_videos_from_index(index_id):
    headers = {
        'x-api-key': TWELVELABS_API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.get(f'{TWELVELABS_BASE_URL}/indexes/{index_id}/videos', headers=headers)
    if response.status_code == 200:
        videos = response.json().get('data', [])
        return videos
    else:
        st.error(f"Failed to retrieve videos from TwelveLabs. Status code: {response.status_code}")
        st.write("Response Content:", response.text)
        st.stop()

def get_video_summary(index_id, video_id):
    data = {
        "video_id": video_id,
        "type": "summary"
    }
    headers = {
        "x-api-key": TWELVELABS_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(f"{TWELVELABS_BASE_URL}/summarize", json=data, headers=headers)
        response.raise_for_status()
        summary = response.json().get('summary', '')
        return summary
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching video summary: {e}")
        st.stop()

# Modified function to return hardcoded transcripts
def get_video_transcript(video_id):
    transcript = transcripts.get(video_id)
    if transcript:
        return transcript
    else:
        st.error(f"Transcript not found for video ID: {video_id}")
        st.stop()

def hallucination_check(transcript, summary):
    prompt = """
    Annotate the hallucinated sections and provide explanations for why they are hallucinations.
    Additionally, calculate the hallucination percentage relative to the total content.
    Your response should be in a structured JSON format, use a single line string, specifying:
    {
      "hallucination_percentage": "0 to 100",
      "hallucinations": [
        {
          "annotated_text": "...",
          "reason_for_hallucination": "..."
        }
      ]
    }
    """
    total = f"Transcript: {transcript}\nSummary: {summary}\n{prompt}"
    headers = {
        "api-key": HALLUCINATION_API_KEY,
        "content-type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": total}
        ]
    }
    response = requests.post(HALLUCINATION_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return content
    else:
        st.error(f"Failed to perform hallucination check. Status code: {response.status_code}")
        st.write("Response Content:", response.text)
        st.stop()

def generate_q(query, video_id):
    import requests

    # Variables
    BASE_URL = "https://api.twelvelabs.io/v1.2"
    api_key = "tlk_14G0MC31C66JK62SNTX2K1MAX2AR"
    data = {
        "prompt": query,
        "video_id": video_id,
    }

    # Send request
    response = requests.post(f"{BASE_URL}/generate", json=data, headers={"x-api-key": api_key})
    r = response.json()
    return r['data']    

def regenerate(hallucinations, query):
    annot = hallucinations["hallucinations"]
    reasons = [i["annotated_text"] for i in annot]
    res = '\n'.join(reasons)
    new_prompt = """"Reduce the hallucination in the answer using thsee annotations: """ + res + query + " regenerate the output"

    return generate_q(new_prompt)

def regenerate_summary(hallucinations, summary):
    annot = hallucinations["hallucinations"]
    reasons = [i["annotated_text"] for i in annot]
    res = '\n'.join(reasons)
    new_prompt = """"Reduce the hallucination in the answer using thsee annotations: """ + res + summary + " regenerate the summary"

    return generate_q(new_prompt)

# def render_video(video_url):
#     hls_player = f"""
#     <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
#     <div style="width: 100%; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
#         <video id="video" controls style="width: 100%; height: auto;"></video>
#     </div>
#     <script>
#       var video = document.getElementById('video');
#       var videoSrc = "{video_url}";
#       if (Hls.isSupported()) {{
#         var hls = new Hls();
#         hls.loadSource(videoSrc);
#         hls.attachMedia(video);
#         hls.on(Hls.Events.MANIFEST_PARSED, function() {{
#           video.pause();
#         }});
#       }}
#       else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
#         video.src = videoSrc;
#         video.addEventListener('loadedmetadata', function() {{
#           video.pause();
#         }});
#       }}
#     </script>
#     """
#     st.components.v1.html(hls_player, height=300)
def render_hls_video(video_url):
    hls_player = f"""
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <div style="width: 100%; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <video id="video" controls style="width: 100%; height: auto;"></video>
    </div>
    <script>
      var video = document.getElementById('video');
      var videoSrc = "{video_url}";
      if (Hls.isSupported()) {{
        var hls = new Hls();
        hls.loadSource(videoSrc);
        hls.attachMedia(video);
      }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
        video.src = videoSrc;
      }}
    </script>
    """
    st.components.v1.html(hls_player, height=300)

def main():
    st.title("Video Summary and Hallucination Checker")

    st.sidebar.header("Select a Video")

    # Fetch the list of videos from the specified index
    videos = get_videos_from_index(INDEX_ID)

    if not videos:
        st.error("No videos available in the specified index.")
        st.stop()

    # Extract video IDs and titles (or filenames)
    video_ids = [video.get('_id') for video in videos]
    video_titles = [video.get('metadata', {}).get('filename', 'Unnamed Video') for video in videos]
    video_hls_urls = [video.get('hls', {}).get('video_url', '') for video in videos] 
    print(video_hls_urls)

    # Create a mapping from video IDs to titles for easy lookup
    video_id_to_title = dict(zip(video_ids, video_titles))
    video_id_to_url = dict(zip(video_ids, video_hls_urls))

    # Create a selectbox for video selection using titles
    selected_video_title = st.sidebar.selectbox("Videos", video_titles)
    # Find the video ID corresponding to the selected title
    selected_video_id = None
    for vid_id, title in video_id_to_title.items():
        if title == selected_video_title:
            selected_video_id = vid_id
            break

    if not selected_video_id:
        st.error("Selected video not found.")
        st.stop()

    st.header(f"Selected Video: {selected_video_title}")

    selected_video_filepath = video_id_to_filepath.get(selected_video_id, "")

    # Display the video using st.video() if the file path exists
    if os.path.exists(selected_video_filepath):
        st.video(selected_video_filepath)
    else:
        st.error("Video file not found. Please check the file path.")


    t1 = st.text_input("Enter the query")
    b2 = st.button("Query")

    if b2 and t1:
        res = generate_q(query=t1, video_id=selected_video_id)
        st.write("Answer")
        st.write(res)


    b1 = st.button("Generate Summary")
    

    summary = ""

    if b1:
        summary = get_video_summary(INDEX_ID, selected_video_id)
        st.subheader("Summary")
        st.write(summary)

    b3 = st.button("Check Hallucination")

    hall = ""

    if b3:
        transcript = get_video_transcript(selected_video_id)
        hall = hallucination_check(summary, transcript)
        st.subheader("Hallucination Check")
        st.write(hall)
    
    b4 = st.button("Regenerate")

    if b4:
        st.write(regenerate_summary(summary=summary, hallucinations=hall))

if __name__ == "__main__":
    main()
