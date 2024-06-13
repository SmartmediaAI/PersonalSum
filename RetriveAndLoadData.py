import pandas as pd
import ast
import re
import random


csv_data = "FILL INN THE PATH TO THE CSV FILE"
storage = "FILL INN THE PATH TO THE STORAGE FOLDER"
df = pd.read_csv(csv_data)

# Function to remove emojis from text


def remove_emojis(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)


# Process each article
for index, row in df.iterrows():
    # Remove emojis from the article
    article_text = remove_emojis(row['Article'])

    # Evaluate the string representation of the list to a list
    qa_list = ast.literal_eval(row['Question_answer'])

    # Select a true QA pair from the current article
    true_qa = random.choice(qa_list)

    # Select false QA pairs from other articles
    false_qas = []
    while len(false_qas) < 2:
        random_row = df.sample(n=1).iloc[0]
        if random_row['Article'] != row['Article']:  # Ensure it's from a different article
            random_qa_list = ast.literal_eval(random_row['Question_answer'])
            false_qas.append(random.choice(random_qa_list))

    # Use the row index as the filename
    filename = f"{index}.txt"

    # Prepare the content for the text file
    content = f"Body:\n{article_text}\n\n"
    content += f"True QA:\nQuestion: {true_qa[0]}\n\nAnswer: {true_qa[1]}\n\n"
    for false_qa in false_qas:
        content += f"False QA:\nQuestion: {false_qa[0]}\n\nAnswer: {false_qa[1]}\n\n"

    # Write the content to a text file
    with open(f'{storage}/{filename}', 'w', encoding='utf-8') as file:
        file.write(content)

print("Files have been created successfully.")
