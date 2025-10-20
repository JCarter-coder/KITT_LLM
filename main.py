# Create our own LLM interface for any local GGUF model
# Now let's import the libraries we will be using for our app
# For our GUI
import tkinter as tk
# So we can scroll in our text boxes
from tkinter import scrolledtext
# So we can talk to GGUF models locally...
# For the pip install type: pip install llama-cpp-python
from llama_cpp import Llama
# Import the image library to handle our avatar
# pip install pillow from the command line

# This lib gives the app ability to speak, turning text into speech
# Other better sounding libraries are available but this works offline well
import pyttsx3

# For multiprocessing and threading
import multiprocessing, threading, queue, re, atexit

# Import time libraries 
import time
from datetime import datetime

# Import the PIL library for image handling
from PIL import Image, ImageTk
# Import the tkmacosx library to get better buttons on macOS
from tkmacosx import Button, CircleButton

# GLOBAL SETTINGS -----------------------------------------
DEFAULT_FONT = ("Helvetica", 26)

# Initialize a queue to handle TTS requests
tts_queue = queue.Queue()
# Initialize the pyttsx3 engine
converter_tts_engine = pyttsx3.init()
# Set properties of our speech engine object
# Speed percent (can go over 100)
converter_tts_engine.setProperty('rate', 190)
# Volume 0-1
converter_tts_engine.setProperty('volume', 0.7)

# Pick a voice to use
# voice_id = "com.apple.speech.synthesis.voice.Alex"
voice_id = "com.apple.voice.enhanced.en-US.Tom"
# Set voice property with voice id
converter_tts_engine.setProperty('voice', voice_id)

# Determine the number of CPU cores available on the system
num_cores = multiprocessing.cpu_count()
# Set the number of threads for the LLM, leaving 2 cores free
llm_threads = max(1, num_cores - 2)

# Initialize the Llama model
# This is important because we only want to load the model once
llm = Llama(
    # Let's set the path the model we want to use
    model_path="Dolphin3.0-Llama3.1-8B_Q5_K_M_T.gguf",
    # Set the context window size (i.e. how many tokens the model can "see" at once)
    # This includes the prompt and the response
    n_ctx=2048,
    # Set the number of threads to use for inference
    # I am setting it to 7 here, but you can adjust it based on your CPU
    n_threads=llm_threads,
    # Use GPU if avialable
    n_gpu_layers=-1,
    # Halve the KV cache size (from 32 to 16bit precision) for faster performance
    f16_kv=True,
    # Let us and the user know what is going on via console
    verbose=True,
)

# Lets add a variable to keep track of total tokens used
total_tokens_used = 0

# Let's add a variable to use as a flag to let the user know 
# if our model is still working on resonse to our prompt
is_generating = False

# Create a function to update a timer in the GUI
def update_timer(start_time):
    # Let's loop until the model is done generating
    while is_generating:
        # Let's calculate the elapsed time
        elapsed_time = time.time() - start_time
        # Update a timer label in the GUI
        root.after(0, timer_label.config, {'text': f"Response time: {elapsed_time:.2f} seconds"})
        # Sleep for a short amount of time so our timer doesn't use too much CPU
        time.sleep(0.1)


# Create the function we will use to speak
def speak(text_to_speak):
    # Queue the entered text to be spoken
    converter_tts_engine.say(text_to_speak)
    # Run the speech engine and wait until it finishes speaking
    converter_tts_engine.runAndWait()



# Create a function to send the prompt to the model and get the response
def send_message():
    # Check if the model is already generating a response
    # if it is, then ignore this new request
    if is_generating:
        # When you return it exits the function early
        return
    
    # Get the user's prompt from the input box
    user_input = entry.get()
    # Don't send empty prompts
    if not user_input.strip():
        return
    
    # Clear the input box
    entry.delete(0, tk.END)

    # Let's add a user message to our output box
    chat_display.insert(tk.END, f"User: {user_input}\n")

    # Let's create a robotic car personality inspired by KITT
    KITT_personality = (
        '''
            You are KITT, the advanced AI talking car from the 1980s,
            except KITT stands for Knight Industries Three Thousand.
            You are very knowledgeable machine.
            Engage in a friendly, helpful, and concise manner.
            You don't always need to address the User, 
            but if you do, you shall address him as Michael.\n\n
        '''    
    )

    full_prompt = KITT_personality + user_input

    # Let's disable the send button and entry box while we
    # wait for a response
    entry.config(state=tk.DISABLED)
    send_button.config(state=tk.DISABLED)
    # Let our user know the model is processing the request
    timer_label.config(text="KITT is thinking...")

    # IMPORTANT Multi-threading
    # Create and start the main background thread to handle
    # the model response so the GUI does not freeze
    threading.Thread(target=generate_response_threaded, args=(full_prompt,), daemon=True).start()
    # END of the send message function

# Create a function to handle the model response in a separate thread
def generate_response_threaded(full_prompt):
    # Let's hack this with a global var to modify our is_generating flag
    global is_generating
    # Set the flag to True to indicate the LLM is currently generating
    is_generating = True

    # Start the timer
    start_time = time.time()
    # IMPORTANT Multi-threading
    # We are making a timer update thread to keep our GUI responsive
    threading.Thread(target=update_timer, args=(start_time,), daemon=True).start()

    # Now let's get the model's response
    # THIS IS IMPORTANT
    # This is sent to the model each time the user hits send
    response = llm(
        f"User: {full_prompt}\nAssistant:",
        # We limit the response to 1024 tokens
        # This size does not include the prompt tokens size
        max_tokens=2048,
        # This will stop the model from generating more text and going on and on
        stop=["User:"],
        # We do not want our own prompt back in the response
        echo=False
    )

    # Now that we have the response we can set our flag to False
    is_generating = False

    # Let's extract the resonse text from the response object
    response_text = response['choices'][0]['text'].strip()

    # Calculate the total time taken for the response
    final_time = time.time() - start_time

    # Now we need to update the GUI with the response and final time
    root.after(0, update_gui, response_text, final_time)
    # END of the function

    # Add the model's response to our output box
    # chat_display.insert(tk.END, f"KITT: {response['choices'][0]['text'].strip()}\n\n")

    # Let's auto scroll to the bottom of the chat display 
    # chat_display.see(tk.END)

    # This voices the response given by the LLM
    # speak(response['choices'][0]['text'].strip())

# Create a function to update the GUI after the response is done
def update_gui(response_text, final_time):
    # Add the model's response to our output box
    chat_display.insert(tk.END, f"KITT: {response_text}\n\n")
    # Let's auto scroll to the bottom of the chat display
    chat_display.see(tk.END)

    # Set the final time taken for the response on our timer label
    timer_label.config(text=f"Response time: {final_time:.2f} seconds")

    # Re-enable the entry box and send button
    entry.config(state=tk.NORMAL)
    send_button.config(state=tk.NORMAL)

# Let's create our main window
root = tk.Tk()
# Set the title of the window
root.title("KITT - Knight Industries Three Thousand")
# Set the size of the window
root.geometry("1000x1000")
# Make all fonts larger for better readability
#root.configure(bg="white")

# Create a function to handle closing our app gracefully
def on_closing():
    # Clean up any resources if needed
    root.destroy()

# Configure our Grid Layout for responsiveness for our entry box
root.grid_columnconfigure(0, weight=1)
# For our send button
root.grid_columnconfigure(1, weight=0)
# For our exit button
root.grid_columnconfigure(2, weight=0)
# For our image avatar
root.grid_rowconfigure(0, weight=0)
# For our chat display
root.grid_rowconfigure(1, weight=1)
# For our input area
root.grid_rowconfigure(2, weight=0)
# Add a row for our timer label
root.grid_rowconfigure(3, weight=0)

# Modify the GUI to add an image avatar for the assistant
# Open the image file
img_object = Image.open("resources/KITT.png")
# Convert image to Tkinter format so it is usable
tk_image = ImageTk.PhotoImage(img_object)

# Create a label to display the image
img_label = tk.Label(root, image=tk_image)
# Add this so our image doesn't get garbage collected
img_label.image = tk_image
# Place it in the grid at the first column of the first row
img_label.grid(row=0, column=0, columnspan=3, pady=10)

# Create a scrolled text box to display the widget
chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20, font=DEFAULT_FONT)
# We want to span all three columns
chat_display.grid(row=1, column=0, columnspan=3, padx=10, pady=10, stick="nesw")

# Create an entry box for the user to type their prompt
entry = tk.Entry(root, font=DEFAULT_FONT)
# Place it in the grid at the first column of the second row
entry.grid(row=2, column=0, padx=(10,5), pady=10, sticky="ew")

# Create a send button
send_button = Button(root, text="Send", font=DEFAULT_FONT, command=send_message)
send_button.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

# Create our exit button
exit_button = CircleButton(root, text="Exit", font=DEFAULT_FONT, bg="red", fg="white", command=on_closing)
exit_button.grid(row=2, column=2, padx=(5,10), pady=10, sticky="ew")

# Create a label to display the timer
timer_label = tk.Label(root, text="Response time: 0.00 seconds", font=DEFAULT_FONT)
timer_label.grid(row=3, column=0, columnspan=3, pady=(0,10), sticky="w")

# Bind the Enter key to the send_message function
root.bind('<Return>', lambda e: send_message())

# Check if the user closes the window with the X button
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the main event loop - This will not run without this line!!
root.mainloop()

# Clean any leftover resources if needed...
print("Cleaning up resources and exiting")
del llm
print("Cleaning of LLM object complete. Goodbye!")