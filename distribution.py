import random

def distribute_questions(marks_distribution: list, topics: list) -> list:
    """
    marks_distribution: list of dicts [{'marks': 5, 'count': 4}, {'marks': 8, 'count': 2}]
    topics: list of dicts [{'topic_name': '...', 'description': '...'}]
    
    Returns a list of question requirements:
    [{'topic_name': '...', 'description': '...', 'marks': 5}, ...]
    """
    question_plan = []
    
    if not topics:
        return question_plan
        
    topic_pool = topics.copy()
    
    for dist in marks_distribution:
        marks = dist.get('marks', 0)
        count = dist.get('count', 0)
        
        for _ in range(count):
            if not topic_pool:
                topic_pool = topics.copy()
            
            selected_topic = random.choice(topic_pool)
            topic_pool.remove(selected_topic)
            
            question_plan.append({
                'topic_name': selected_topic.get('topic_name', 'Unknown Topic'),
                'description': selected_topic.get('description', ''),
                'marks': marks
            })
            
    return question_plan
