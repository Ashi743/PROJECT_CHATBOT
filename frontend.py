import streamlit as st
from backend import chatbot
from langchain.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

CONFIG11 = RunnableConfig(configurable={"thread_id": "thread-1"})

#message =['user' , 'content':user-input]

#to append in  streamlit based stateful session dict 

#1 create a sessional message_history dict
if "message_history" not in st.session_state:
    st.session_state["message_history"]= []

#2 to read pvs messages in histORY and display in chat format
for messages in st.session_state["message_history"]:
    with st.chat_message(messages['role']):
        st.text(messages['content'])
        
# 3 new ammends
user_input= st.chat_input("type here")

if user_input:
    ## user input 
    st.session_state["message_history"].append({'role':'user', 'content':user_input})
    with st.chat_message("user"):
        st.text(user_input)

    ## invoke the chatbot with the user input and get response from the backend 
    response= chatbot.invoke({'messages':[HumanMessage(content=user_input)]}, config=CONFIG11)
    ai_message= response["messages"][-1].content


    ## append the ai response to the message history using the checkpointer and display in chat format 
    st.session_state["message_history"].append({'role':'assistant', 'content':ai_message})
    with st.chat_message("assistant"):
        st.text(ai_message)
        