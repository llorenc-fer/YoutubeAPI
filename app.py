from googleapiclient.discovery import build
import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

# def add_bg_from_url():
#     st.markdown(
#         f"""
#         <style>
#         .stApp {{
#             background-image: url("https://github.com/llorenc-fer/NYC-Collisions/blob/main/pexels-photo-7567529.png?raw=true");
#             background-attachment: fixed;
#             background-size: cover
#         }}
#         </style>
#         """,
#         unsafe_allow_html=True
#     )
# add_bg_from_url()


api_key = 'AIzaSyAGvRPcBwmeNvHY3WtlLQEu9Wi-SZz87t8'
st.title("Youtube Quick-Stats App")
#-------------CHANNEL COMPARATOR--------------------------------------------
#channel_id = 'UCnz-ZXXER4jOvuED5trXfEA'

# ['UCnz-ZXXER4jOvuED5trXfEA', # techTFQ
#                'UCLLw7jmFsvfIVaUFsLs8mlQ', # Luke Barousse 
#                'UCiT9RITQ9PW6BhXK0y2jaeg', # Ken Jee
#                'UC7cs8q-gJRlGwj4A8OmCmXg', # Alex the analyst
#                'UC2UXDak6o7rBm23k3Vv5dww', # Tina Huang
#                'UCy5znSnfMsDwaLlROnZ7Qbg',  # Dot CSV
#               ]

youtube = build('youtube', 'v3', developerKey=api_key)



#----------------CHANNEL ANALYZER--------------------
url = 'https://support.google.com/youtube/answer/3250431?hl=en'
radio_markdown = (
'Channel ID can be found at the url of your own channel'
).strip()
input3 = st.text_input('Enter Channel ID: ', 'UCy5znSnfMsDwaLlROnZ7Qbg', help=radio_markdown)
with st.expander("*About Channel IDs*"):
        st.write("Your own channel ID can be found at the url of your own youtube profile. More info [here](%s)." % url)
        st.write("""
                Here are some more IDs to check the app:\n
                UCLLw7jmFsvfIVaUFsLs8mlQ\n
                UCiT9RITQ9PW6BhXK0y2jaeg\n
                UC7cs8q-gJRlGwj4A8OmCmXg\n
                UC2UXDak6o7rBm23k3Vv5dww\n
        """)        


channel_ids = [input3]

def get_channel_stats(youtube, channel_ids):
    """
    Get channel statistics: title, subscriber count, view count, video count, upload playlist
    Params:
    youtube: the build object from googleapiclient.discovery
    channels_ids: list of channel IDs
    Returns:
    all_data containing the channel statistics for all channels in the provided list: title, subscriber count, view count, video count, upload playlist
    """
    
    request = youtube.channels().list(
                part='snippet,contentDetails,statistics',
                id=','.join(channel_ids))
    response = request.execute() 
    
    data = dict(Channel_name = response['items'][0]['snippet']['title'],
                    Subscribers = response['items'][0]['statistics']['subscriberCount'],
                    Views = response['items'][0]['statistics']['viewCount'],
                    Total_videos = response['items'][0]['statistics']['videoCount'],
                    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])
    
    
    return data



channel_statistics = get_channel_stats(youtube, channel_ids)

#Convert into DF
channel_data = pd.DataFrame([channel_statistics])

#Convert to numeric
channel_data['Subscribers'] = pd.to_numeric(channel_data['Subscribers'])
channel_data['Views'] = pd.to_numeric(channel_data['Views'])
channel_data['Total_videos'] = pd.to_numeric(channel_data['Total_videos'])


playlist_id = channel_data.iloc[0]['playlist_id']

def get_video_ids(youtube, playlist_id):
    
    request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId = playlist_id,
                maxResults = 50)
    response = request.execute()
    
    video_ids = []
    
    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])
        
    next_page_token = response.get('nextPageToken')
    more_pages = True
    
    while more_pages:
        if next_page_token is None:
            more_pages = False
        else:
            request = youtube.playlistItems().list(
                        part='contentDetails',
                        playlistId = playlist_id,
                        maxResults = 50,
                        pageToken = next_page_token)
            response = request.execute()
    
            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])
            
            next_page_token = response.get('nextPageToken')
        
    return video_ids

video_ids = get_video_ids(youtube, playlist_id)

def get_video_details(youtube, video_ids):
    all_video_stats = []
    
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
                    part='snippet,statistics',
                    id=','.join(video_ids[i:i+50]))
        response = request.execute()
        
        for video in response['items']:
            video_stats = dict(Title = video['snippet']['title'],
                                Published_date = video['snippet']['publishedAt'],
                                Views = video['statistics']['viewCount'],
                                Likes = video['statistics']['likeCount'],
                                Comments = video['statistics']['commentCount']
                                )
            all_video_stats.append(video_stats)
    
    return all_video_stats

video_details = get_video_details(youtube, video_ids)

#convert into DF
video_data = pd.DataFrame(video_details)

#convert columns to numeric
video_data['Published_date'] = pd.to_datetime(video_data['Published_date']).dt.date
video_data['Views'] = pd.to_numeric(video_data['Views'])
video_data['Likes'] = pd.to_numeric(video_data['Likes'])
video_data['Views'] = pd.to_numeric(video_data['Views'])

#Sort by total views
top10_videos = video_data.sort_values(by='Views', ascending=False).head(10)

#Add column with month
video_data['Month'] = pd.to_datetime(video_data['Published_date']).dt.strftime('%b')

#Group by month
videos_per_month = video_data.groupby('Month', as_index=False).size()
sort_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
videos_per_month.index = pd.CategoricalIndex(videos_per_month['Month'], categories=sort_order, ordered=True)
videos_per_month = videos_per_month.sort_index()

#----------------------------------STATS----------------------------------------------------------------------
st.write("Channel Name: ", channel_statistics['Channel_name'])

st.write('Last Videos:')
st.dataframe(video_data)



#----------------------------------PLOTS----------------------------------------------------------------------

#Plot top10 videos
fig = px.histogram(top10_videos, 
                    x ="Views", 
                    y='Title', 
                    template='plotly_white', 
                    title="Channel Views",
                    color_discrete_sequence=["red"]) 
fig.update_layout(title="Top 10 most viewed videos", 
                    xaxis_title="Views", 
                    yaxis_title="Title", 
                    template = 'plotly_dark')
fig.update_layout(yaxis={'categoryorder':'total ascending'}) 
fig.update_xaxes(minor=dict(showgrid=True))
st.plotly_chart(fig)

#Plot views
fig2 = px.histogram(videos_per_month, 
                            x ="Month", 
                            y='size', 
                            template='plotly_white', 
                            title="Channel Views",
                            color_discrete_sequence=["red"]) 
fig2.update_layout(title="Channel Views", 
                    xaxis_title="Month", 
                    yaxis_title="Size", 
                    template = 'plotly_dark')
st.plotly_chart(fig2)


#download csv streamlit
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv()#.encode('utf-8')
video_data.to_csv('Youtube_History.csv')

csv = convert_df(video_data)

st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name='Youtube_History.csv',
    mime='text/csv',
)