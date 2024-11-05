# YouTube Video Download Management and Conversation Platform

##      Introduction
Users can download Chinese videos locally according to the download link, automatically recognize video subtitles and generate video subtitle files, and realize dynamic management of videos in the video library page.   

Users can search for several video texts that are most relevant to the keywords typed in by semantic search, quickly search for their target video and play and view the subtitle text.  

Provide a multi-round generative model dialog service for a specific particular video.

## Installation Instructions
Describe how to install and run the project. May include steps to clone the repository and commands to install dependencies:
```bash
git clone https://github.com/xjwithtender/youtube_video.git
cd youtube_video
pip install -r requirements.txt
```

## Instructions
First, to enable the app you need to wake up the streamlit app by typing the command “streamlit run streamlit_app.py” in the terminal.

Depending on the target task it can be divided into four subpages: YouTube video download, YouTube video library, audio/video subtitle text retrieval and audio/video subtitle multi-round dialog.  

Enter the corresponding paging task as required.
### YouTube Video Download
Enter a number of space-separated video links in the prompt box, check “Download best quality MP4 files” and click Download to run the task on this page.

### YouTube video library
The web page displays locally stored videos directly, with a number of control buttons at the bottom of each video to control the video playback, volume level and speed.  

Click the “Delete” button to remove the video from the local video. 
Click on “View Subtitles” to view the text of the subtitles stored in the database.

### Video Subtitle Text Retrieval
Enter a number of keywords in the prompt box that you want to search for video content, and click “Start Searching” to run the page task.

### Multi-Round Dialog with Video Captioning
The “Select Video” drop-down menu displays the videos stored in the local video library, and the first file in the database is selected by default.

For the video in the menu, you can enter the content of the conversation you want to have in the next column, “Please enter a dialog”, and click “Send” to receive the model's reply.  

Retype the new content and hit send to display the history of the conversation and the latest model replies.  

If a new video is selected in the “Select Video” drop-down menu, the multi-round dialog will restart with the previous history clear.


