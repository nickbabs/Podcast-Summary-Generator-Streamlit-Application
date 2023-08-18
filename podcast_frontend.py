import streamlit as st
import modal
import json
import os

def main():
    st.title("Welcome to Nick's Dashboard for Podcast Summaries")

    available_podcast_info = create_dict_from_json_files('.')

    # Left section - Input fields
    st.sidebar.header("Podcast & RSS Feeds")

    # Dropdown box
    st.sidebar.subheader("Already Available Podcasts")
    selected_podcast = st.sidebar.selectbox("Select Desired Podcast Below", options=available_podcast_info.keys())

    if selected_podcast:

        podcast_info = available_podcast_info[selected_podcast]

        # Right section - Newsletter content
        st.header("Newsletter Content")

        # Display the podcast title
        st.subheader("Podcast Episode Title")
        st.write(podcast_info['podcast_details']['episode_title'])

        # Display the podcast summary and the cover image in a side-by-side layout
        col1, col2 = st.columns([8, 2])

        with col1:
            # Display the podcast episode summary
            st.subheader("Episode Summary")
            st.write(podcast_info['podcast_summary'])

        with col2:
            st.image(podcast_info['podcast_details']['episode_image'], caption="Podcast Cover", width=300, use_column_width=True)

        # Display the podcast guest and their details in a side-by-side layout
        col3, col4 = st.columns([3, 7])

        with col3:
            st.subheader("Guest or Significant Person in this Episode")
            st.write(podcast_info['podcast_guest']['name'])

        with col4:
            st.subheader("Who are they?")
            st.write(podcast_info["podcast_guest"]['summary'])

    # User Input box
    st.sidebar.subheader("Process a New Podcast Below")
    url = st.sidebar.text_input("Paste the Link to the Podcast's RSS Feed")

    process_button = st.sidebar.button("Submit")
    st.sidebar.markdown("**Note**: Podcast processing can take up to 5 minutes.")

    if process_button:

        # Call the function to process the URLs and retrieve podcast guest information
        podcast_info = process_podcast_info(url)

        # Right section - Newsletter content
        st.header("Newsletter Content")

        # Display the podcast title
        st.subheader("Podcast Episode Title")
        st.write(podcast_info['podcast_details']['episode_title'])

        # Display the podcast summary and the cover image in a side-by-side layout
        col1, col2 = st.columns([8, 2])

        with col1:
            # Display the podcast episode summary
            st.subheader("Episode Summary")
            st.write(podcast_info['podcast_summary'])

        with col2:
            st.image(podcast_info['podcast_details']['episode_image'], caption="Podcast Cover", width=300, use_column_width=True)

        # Display the podcast guest and their details in a side-by-side layout
        col3, col4 = st.columns([3, 7])

        with col3:
            st.subheader("Guest or Significant Person in this Episode")
            st.write(podcast_info['podcast_guest']['name'])

        with col4:
            st.subheader("Who are they?")
            st.write(podcast_info["podcast_guest"]['summary'])

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
        
        def process_podcast_info(url):
            f = modal.Function.lookup("corise-podcast-project", "process_podcast")
            output = f.call(url, '/content/podcast/')
            return output

if __name__ == '__main__':
    main()
