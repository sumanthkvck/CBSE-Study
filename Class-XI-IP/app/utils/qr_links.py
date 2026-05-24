"""
Reference links for KIPS Informatics Practices Class XI chapters.
Points to CBSE/DIKSHA resources relevant to each chapter topic.
"""

CHAPTER_LINKS = {
    1:  {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 1: Computer System — CBSE Study Material"},
    2:  {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 2: Programming with Python — CBSE Study Material"},
    3:  {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 3: Python Basics — CBSE Study Material"},
    4:  {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 4: Data Types and Operators — CBSE Study Material"},
    5:  {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 5: Control Flow Statements — CBSE Study Material"},
    6:  {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 6: List Manipulation — CBSE Study Material"},
    7:  {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 7: Python Dictionary — CBSE Study Material"},
    8:  {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 8: Database Concepts — CBSE Study Material"},
    9:  {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 9: Structured Query Language — CBSE Study Material"},
    10: {"url": "https://diksha.gov.in/explore?subject=Informatics%20Practices&gradeLevel=Class%2011", "label": "Ch 10: Emerging Trends in Technology — CBSE Study Material"},
}


def get_link(chapter_num: int) -> dict | None:
    return CHAPTER_LINKS.get(chapter_num)
