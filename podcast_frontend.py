import streamlit as st
import modal
import json
import os

def main():
    st.title("Welcome to Nick's Dashboard for Generating Podcast Summaries")
    
    # Right section - Newsletter content
    st.header("Let's get started...")
    st.write("""**August 28, 2023:  At this time, please process podcasts with shorter episodes, ideally under 25 minutes**.
                Larger episodes are at risk of timing out and using up this page's limited credits. However, feel free to explore the pre-generated summaries in the dropdown!""")
    st.write("""Generate a summary about your favorite podcast's most recent episode on my page! At the
                left side of the screen, simply copy and paste the link to your podcast's RSS feed and click process. 
                To find your podcast's RSS feed, search for your podcast's title on a podcast search engine
                website such as [listennotes.com](https://www.listennotes.com/) and find the section that says RSS
                feed. This should provide you with a URL to the podcast's RSS feed.""")

    available_podcast_info = create_dict_from_json_files('.')

    # Left section - Input fields
    st.sidebar.header("Podcast & RSS Feeds")

    # Dropdown box
    st.sidebar.subheader("Examples of How Your Summary Will Look")
    selected_podcast = st.sidebar.selectbox("Select from list of example podcast summaries below.", options=available_podcast_info.keys())
    # User Input box
    st.sidebar.subheader("Processing Your Podcast")
    url = st.sidebar.text_input("Paste the link to your desired podcast's RSS feed below.")
    process_button = st.sidebar.button("Process", disabled = False)
    st.sidebar.write("Process button to be disabled this week, will go live again at a later date.")
    
    st.sidebar.markdown("""Note: Processing your podcast can take up to 5 minutes.
                        **Please understand API credits are limited for this page and will run out soon.**""")
    
    if selected_podcast and not process_button:
        podcast_info = available_podcast_info[selected_podcast]
        # Function to display podcast details
        display_podcast_details(podcast_info)

    if process_button:
        # Call the function to process the URLs and retrieve podcast guest information
        podcast_info = process_podcast_info(url)
        # Display the podcast details
        display_podcast_details(podcast_info)

def create_dict_from_json_files(folder_path):
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    data_dict = {}

    for file_name in json_files:
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'r') as file:
            podcast_info = json.load(file)
            podcast_name = podcast_info['podcast_details']['podcast_title']
            # Process the file data as needed
            data_dict[podcast_name] = podcast_info

    return data_dict

def display_podcast_details(podcast_info):
    st.header(podcast_info['podcast_details']['podcast_title'])
    # Display the podcast title
    st.subheader("Episode Title")
    st.write(podcast_info['podcast_details']['episode_title'])
    
    # Display the podcast image
    caption = podcast_info['podcast_details']['podcast_title']
    st.image(podcast_info['podcast_details']['episode_image'], caption = caption, width=270, use_column_width=False)
    
    # Display the podcast episode summary
    st.subheader("Episode Summary")
    st.write(podcast_info['podcast_summary'])

    # Display the guest and their details in a side-by-side layout
    col1, col2 = st.columns([4, 6])    
    with col1:
        st.subheader("Episode Guest or Significant Person")
        if podcast_info['podcast_guest']['name'] is None:
            st.write("Name:  Unkown")
        else:
            st.write("Name:  ", podcast_info['podcast_guest']['name'])
        if podcast_info['podcast_guest']['org'] is None:
            st.write("Organization:  Unkown")
        else:
            st.write("Organization:  ", podcast_info['podcast_guest']['org'])
        if podcast_info['podcast_guest']['title'] is None:
            st.write("Position Held:  Unkown")
        else:
            st.write("Position Held:  ", podcast_info['podcast_guest']['title'])

    with col2:
        st.subheader("Wikipedia Summary")
        st.write(podcast_info["podcast_guest"]['summary'])

    
def process_podcast_info(url):
    f = modal.Function.lookup("corise-podcast-project", "process_podcast")
    output = f.call(url, '/content/podcast/')
    return output

if __name__ == '__main__':
    main()
