# PersonalSum

PersonalSum: A User-Subjective Guided Personalized Summarization Dataset for Large Language Models

## Overview

This repository contains the code and data for the research project "PersonalSum: A User-Subjective Guided Personalized Summarization Dataset for Large Language Models." This project aims to create a high-quality, personalized summarization dataset and investigate the differences between generic machine-generated summaries and those personalized to individual users' preferences.

## Repository Structure

The repository is structured as follows:

```
.
├── AssignmentFilter.py
├── BanFilter.py
├── HITOrganizer.py
├── README.md
├── dataset
│   ├── PersonalSum_original.csv
│   └── Topic_centric_PersonalSum.csv
├── main.ipynb
├── mturk_helpers.py
├── old_main_with_definitions.ipynb
└── requirements.txt
```

### Files and Directories

- `AssignmentFilter.py`: Contains the `AssignmentFilter` class used to filter assignments based on various quality metrics.
- `BanFilter.py`: Contains the `BanFilter` class used to identify workers who consistently submit low-quality work.
- `HITOrganizer.py`: Contains the `HITOrganizer` class used to organize HIT (Human Intelligence Task) files and move them based on approval status.
- `main.ipynb`: A Jupyter Notebook that ties together the functionalities of other scripts to filter, approve, reject, and organize assignments in an interactive format.
- `mturk_helpers.py`: Contains helper functions used to manage MTurk HITs, such as creating HITs, processing directories, and handling qualifications.
- `old_main_with_definitions.ipynb`: An older version of the main notebook with all function definitions included.
- `README.md`: This file.
- `dataset/`: Directory containing the original and topic-centric datasets.
  - `PersonalSum_original.csv`: The original dataset.
  - `Topic_centric_PersonalSum.csv`: The topic-centric dataset.
- `requirements.txt`: Lists the dependencies required to run the project.

## Setup and Installation

To run the project, you need to have Python installed on your system. It's recommended to use a virtual environment to manage dependencies.

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/PersonalSum.git
   cd PersonalSum
   ```

2. **Create a virtual environment:**

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

## Usage

### Filtering Assignments

To filter assignments based on various quality metrics, use the `AssignmentFilter` class. This class checks for several criteria such as duration of task, language used, and quality of summaries.

Example usage:

```python
from AssignmentFilter import AssignmentFilter

folder_path = 'path/to/your/data'
assignment_filter = AssignmentFilter(folder_path)
filtered_assignment_ids = assignment_filter.filter_assignments()

print(f"Filtered {len(filtered_assignment_ids)} assignments:")
for assignment_id in filtered_assignment_ids:
    print(assignment_id)
```

### Banning Workers

To identify and ban workers who consistently submit low-quality work, use the `BanFilter` class.

Example usage:

```python
from BanFilter import BanFilter

folder_path = 'path/to/your/data'
ban_filter = BanFilter(folder_path)
filtered_worker_ids = ban_filter.get_worker_ids()

print(f"Banned {len(filtered_worker_ids)} workers:")
for worker_id in filtered_worker_ids:
    print(worker_id)
```

### Organizing HIT Files

To organize HIT files based on approval status, use the `HITOrganizer` class.

Example usage:

```python
from HITOrganizer import HITOrganizer

parsed_hits_dir = 'path/to/parsed/hits'
user_profiles_dir = 'path/to/user/profiles'
hit_organizer = HITOrganizer(parsed_hits_dir, user_profiles_dir)

# Organize a specific assignment
assignment_id = 'your_assignment_id'
hit_organizer.organize_file(assignment_id, approve=True)
```

### MTurk Helpers

The `mturk_helpers.py` file contains various functions to handle MTurk HITs. Import the required functions in your script or notebook as needed.

Example usage:

```python
from mturk_helpers import *

# Initialize MTurk client
load_dotenv()  # This loads the environment variables from .env
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
region_name = 'us-east-1'
endpoint_url = 'https://mturk-requester.us-east-1.amazonaws.com'

mturk = boto3.client(
    'mturk',
    endpoint_url=endpoint_url,
    region_name=region_name,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
)

# Print account balance
print(mturk.get_account_balance()['AvailableBalance'])

# Example to process directory in chunks
input_directory = 'path/to/your/input_directory'
output_directory = 'path/to/your/output_directory'
process_directory_in_chunks(input_directory, output_directory)
```

### Jupyter Notebook

The `main.ipynb` provides the same functionalities as the scripts but in an interactive Jupyter Notebook format. You can run and modify the notebook cells to process the assignments step by step.

To open the notebook, run:

```sh
jupyter notebook main.ipynb
```

## Datasets

The `dataset` directory contains two CSV files:

- `PersonalSum_original.csv`: The original dataset with personalized summaries.
- `Topic_centric_PersonalSum.csv`: The dataset organized around specific topics.

The dataset is designed to support research in the domain of personalized textual summarization. It offers high quality, manually annotated news summaries that reflect individual users preferences and focuses. The dataset is constructed to facilitate the development of personalized summarization models, filling the gap in existing research, which often relies on generic summaries or pseudo datasets. PersonalSum allows for the exploration of how personal interests and preferences can be incorporated into summarization tasks.

## Functions of the Dataset

1. **Personalized Summarization**: Facilitates the creation of summaries that align with individual user preferences by incorporating user profiles and personalized annotations.
2. **Generic Summarization**: Includes machine generated summaries for comparative analysis with personalized summaries.

## Dataset Structure

The dataset consists of two primary CSV files, each serving distinct purposes:

1. **PersonalSum_original.csv**: The original dataset with personalized summaries created by human annotators reflecting their personal interests and preferences. This file also includes user profiles and the source sentences from the articles.
2. **Topic_centric_PersonalSum.csv**: The dataset organized around specific topics, allowing for focused analysis and comparison across different thematic areas. The data in this file is almost identical to PersonalSum_original.csv, with the key difference being that each assignment had the same topic. This structure aims to investigate the correlation between the quality of summaries and the users topic preferences.

### Difference Between the Two CSV Files

- **PersonalSum_original.csv**: 
  - Contains human annotated summaries that reflect individual user preferences.

- **Topic_centric_PersonalSum.csv**: 
  - Organizes summaries around specific topics.
  - Facilitates analysis and comparison of summaries within specific thematic areas.
  - The data collection was performed after PersonalSum_original.csv, with each assignment focused on the same topic to examine the potential correlation between summary quality and users topic preferences.

## Main Attributes of the Dataset

- **User Profiles**: Each annotator is assigned a unique WorkerID, which identifies the individual performing the annotation. This allows tracking of annotations by the same person across different tasks.
- **AssignmentID**: Represents a specific annotation task. Each annotator summarizes three different news articles under the same AssignmentID, indicating that they were part of the same annotation session.
- **Duration**: Indicates the total time taken by each worker to complete an annotation assignment. The duration is the combined time used for finishing the annotations of three news articles.
- **Summaries**: Both generic and personalized summaries with corresponding source sentences from news articles are provided.
- **Question Answer Sets**: Three question and answer pairs related to each article are included, correlating directly to the content of the articles.

## License

This dataset is made available under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) license. You are free to share and adapt the material for non-commercial purposes as long as appropriate credit is given, and any changes made are indicated.

## Contact

For any questions or issues, please contact [your_email@example.com].
