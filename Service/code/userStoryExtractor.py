from typing import List
import pandas as pd


class UserStoryExtractor:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        
    def extract_user_stories(self) -> List[str]:
        """Extract user stories from the Excel file."""
        try:
            df = pd.read_excel(self.excel_path)
            if 'user_story' not in df.columns:
                raise ValueError("Excel file doesn't contain 'user_story' column")
            
            # Remove NaN values and convert to list
            user_stories = df['user_story'].dropna().tolist()
            return user_stories
        except Exception as e:
            print(f"Error extracting user stories: {e}")
            return []