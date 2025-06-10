# Change this part at the top of the file
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Add this simple route for testing
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'message': 'Oakbot backend is running!'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Welcome to Oakbot API!',
        'endpoints': {
            '/chat': 'POST - Send a message to the chatbot',
            '/health': 'GET - Check API health'
        }
    })

# Move the LangChain imports here to avoid startup errors
try:
    from langchain.chains import LLMChain
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import PromptTemplate
    from langchain.chat_models import ChatOpenAI
    
    # Initialize your chatbot components
    knowledge_context = """
    Northeastern University Information:
    - Founded in 1898 in Boston, Massachusetts
    - Known for cooperative education (co-op) program
    - Offers undergraduate and graduate programs
    - Campus locations in Boston, Charlotte, London, Toronto, Vancouver, and more
    - Mascot: King Husky
    - Colors: Red and Black
    - Popular programs: Engineering, Business, Computer Science, Health Sciences
    """

    prompt_template = PromptTemplate(
        input_variables=["history", "input"],
        template=f"""
        You are Oakbot, a helpful assistant for Northeastern University students with access to the following knowledge base:

        {knowledge_context}

        Conversation history:
        {{history}}

        User query:
        {{input}}

        Provide the most relevant and accurate response to the user query. Be friendly, helpful, and specific to Northeastern University. Keep responses concise but informative.
        """
    )

    # Initialize LLM and memory
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        temperature=0,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    memory = ConversationBufferMemory(memory_key="history", return_messages=True)

    conversation = LLMChain(
        llm=llm,
        prompt=prompt_template,
        memory=memory
    )
    
    langchain_loaded = True
except Exception as e:
    print(f"Error loading LangChain: {e}")
    langchain_loaded = False

events_calendar_link = "https://outlook.office365.com/calendar/published/6b0d6d7d1cac4e7c87760b7b8802fc09@northeastern.edu/08cbbcccb8f34b76833c3bac4e30967812111475007683985818/calendar.html"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Check if LangChain loaded successfully
        if not langchain_loaded:
            return jsonify({'response': 'Sorry, the AI service is currently unavailable. Please try again later.'}), 200
        
        # Check for special cases
        if any(keyword in user_message.lower() for keyword in ["event", "happening", "calendar", "schedule"]):
            response = f"Check out upcoming Northeastern events here: {events_calendar_link}"
        elif "feedback" in user_message.lower():
            response = "I'd love to hear your feedback! Please share it here: https://forms.gle/d5wvGxGH7A6uCsBH7"
        else:
            # Get response from LangChain
            response = conversation.run(user_message)
        
        return jsonify({'response': response})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=False, host='0.0.0.0', port=port)
