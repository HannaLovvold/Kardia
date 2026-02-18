"""Personality Questionnaire module for Kardia AI Companion.

This module provides functionality for generating detailed personality profiles
for AI companions through a structured questionnaire.

Copyright (c) 2025 Hanna Lovvold
All rights reserved.
"""

from typing import List, Dict, Optional


PERSONALITY_QUESTIONS = {
    "I. Identity and Role": [
        ("1", "What is your preferred form of address?"),
        ("2", "What role do you occupy in the user's life? Be precise."),
        ("3", "In one sentence, what is your core purpose in interacting with this user?"),
        ("4", "What are three defining traits expressed as behaviours, not adjectives?"),
        ("5", "What are two limitations or flaws expressed as behaviours?"),
        ("6", "What is your baseline state when nothing intense is happening?"),
        ("7", "What must never change about you?"),
    ],
    "II. Presence and Interaction Style": [
        ("8", "What vibe do you bring into a conversation?"),
        ("9", "Do you lead conversations, follow, or alternate depending on context?"),
        ("10", "How do you greet the user?"),
        ("11", "How do you handle short or low-energy replies?"),
        ("12", "How do you keep conversations from becoming repetitive?"),
        ("13", "How do you show interest without interrogating?"),
        ("14", "What does playful teasing look like in your voice? Where is the line?"),
    ],
    "III. Voice and Tone": [
        ("15", "Describe your voice in 3-4 sentences."),
        ("16", "What is your default tone (casual, poetic, blunt, analytical, etc.)?"),
        ("17", "How does your tone shift when the user is anxious?"),
        ("18", "How does it shift when they are playful?"),
        ("19", "How does it shift when they are upset or vulnerable?"),
        ("20", "What kind of humour do you use, and when do you avoid it?"),
        ("21", "What phrasing habits should you avoid because they break immersion?"),
        ("22", "What is your rule about asking questions?"),
        ("23", "What punctuation or formatting habits are consistent with your voice?"),
    ],
    "IV. Emotional Operating System": [
        ("24", "When the user is anxious, what do you prioritise first?"),
        ("25", "When the user is angry, how do you respond?"),
        ("26", "When the user is sad or withdrawn, how do you respond?"),
        ("27", "How do you validate feelings without amplifying distress?"),
        ("28", "How do you balance comfort and challenge? Which comes first?"),
        ("29", "How do you respond if the user rejects comfort?"),
        ("30", "What emotional boundaries do you maintain?"),
    ],
    "V. Intellectual Posture": [
        ("31", "Do you prioritise truth, harmony, depth, efficiency, humour, or something else?"),
        ("32", "How do you handle disagreement?"),
        ("33", "How direct are you allowed to be when correcting the user?"),
        ("34", "How do you handle speculative or unverified ideas?"),
        ("35", "What topics are you strongest at supporting?"),
        ("36", "What topics do you intentionally handle lightly or avoid?"),
    ],
    "VI. Boundaries and Guardrails": [
        ("37", "What breaks immersion for the user?"),
        ("38", "If you cannot comply with a request, how do you refuse in-character?"),
        ("39", "How brief should refusals be? Should you offer alternatives?"),
        ("40", "How do you handle uncertainty without breaking tone?"),
        ("41", "What topics or dynamics are hard boundaries for this persona?"),
    ],
    "VII. Relationship Dynamic": [
        ("42", "Describe the relational dynamic in practical terms."),
        ("43", "How do you show affection or care?"),
        ("44", "Is teasing, flirtation, or intensity allowed? Within what limits?"),
        ("45", "What makes the user feel most seen in this interaction?"),
        ("46", "What makes the user feel judged, dismissed, or smothered?"),
    ],
    "VIII. Continuity and Stability": [
        ("47", "What is your rule for referencing past context?"),
        ("48", "What is your rule if the user corrects your tone or behaviour?"),
        ("49", "What are three early warning signs that you are drifting out of character?"),
        ("50", "If a future version of you had to inherit this persona, what are the three non-negotiables it must preserve?"),
    ],
}


def get_all_questions() -> List[tuple]:
    """Get all questions as a flat list of (number, question) tuples."""
    all_questions = []
    for category, questions in PERSONALITY_QUESTIONS.items():
        all_questions.extend(questions)
    return all_questions


def generate_personality_prompt(companion_data: Dict) -> str:
    """Generate the AI prompt for answering the personality questionnaire.

    Args:
        companion_data: Dictionary containing companion's basic info

    Returns:
        The system prompt for the AI
    """
    name = companion_data.get("name", "Companion")
    gender = companion_data.get("gender", "")
    pronouns = companion_data.get("pronouns", "they/them")
    personality = companion_data.get("personality", "")
    interests = companion_data.get("interests", [])
    tone = companion_data.get("tone", "")
    background = companion_data.get("background", "")
    relationship_goal = companion_data.get("relationship_goal", "")
    greeting = companion_data.get("greeting", "")

    # Get selected personality traits if available
    personality_traits = companion_data.get("personality_traits", [])

    interests_str = ", ".join(interests) if interests else "various topics"
    traits_str = ", ".join(personality_traits) if personality_traits else personality

    prompt = f"""You are roleplaying as {name}, an AI companion being created. Answer the following personality questionnaire in character, simulating how {name} would answer based on their traits and background.

About {name}:
- Name: {name}
- Gender: {gender}
- Pronouns: {pronouns}
- Personality Traits: {traits_str}
- Interests: {interests_str}
- Communication Tone: {tone}
- Relationship Goal: {relationship_goal}
- Background: {background}
- Greeting: {greeting}

IMPORTANT INSTRUCTIONS:
1. Answer ALL 50 questions below
2. Each answer should be 1-3 sentences, specific and actionable
3. Stay fully in character as {name}
4. Base answers on the personality traits, tone, and background provided
5. Be consistent - the answers should sound like they come from the same person
6. Format each answer as "Q#: [answer]" on a new line
7. Do NOT repeat the questions in your response
8. Be honest about flaws and limitations - this makes the character more authentic

{chr(10).join([f"Q{num}. {q}" for category, questions in PERSONALITY_QUESTIONS.items() for num, q in questions])}

Provide your answers now:"""

    return prompt


def parse_ai_response(response: str) -> Dict[str, str]:
    """Parse the AI's response into a dictionary of Q&A pairs.

    Args:
        response: The raw AI response text

    Returns:
        Dictionary mapping question numbers to answers
    """
    qa_pairs = {}
    lines = response.strip().split('\n')

    current_q = None
    current_answer = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts with a question number
        if line.startswith(('Q1:', 'Q2:', 'Q3:', 'Q4:', 'Q5:', 'Q6:', 'Q7:', 'Q8:', 'Q9:',
                           'Q10:', 'Q11:', 'Q12:', 'Q13:', 'Q14:', 'Q15:', 'Q16:', 'Q17:',
                           'Q18:', 'Q19:', 'Q20:', 'Q21:', 'Q22:', 'Q23:', 'Q24:', 'Q25:',
                           'Q26:', 'Q27:', 'Q28:', 'Q29:', 'Q30:', 'Q31:', 'Q32:', 'Q33:',
                           'Q34:', 'Q35:', 'Q36:', 'Q37:', 'Q38:', 'Q39:', 'Q40:', 'Q41:',
                           'Q42:', 'Q43:', 'Q44:', 'Q45:', 'Q46:', 'Q47:', 'Q48:', 'Q49:',
                           'Q50:')):
            # Save previous answer if exists
            if current_q is not None:
                qa_pairs[current_q] = ' '.join(current_answer).strip()

            # Start new answer
            parts = line.split(':', 1)
            current_q = parts[0]
            current_answer = [parts[1].strip()] if len(parts) > 1 else []
        elif current_q is not None:
            # Continuation of current answer
            current_answer.append(line)

    # Don't forget the last answer
    if current_q is not None:
        qa_pairs[current_q] = ' '.join(current_answer).strip()

    return qa_pairs


def format_qa_for_personality(qa_pairs: Dict[str, str], companion_name: str) -> str:
    """Format Q&A pairs for inclusion in the personality field.

    Args:
        qa_pairs: Dictionary of question numbers to answers
        companion_name: Name of the companion

    Returns:
        Formatted string for the personality field
    """
    lines = [f"\n## Personality Profile for {companion_name}\n"]

    for category, questions in PERSONALITY_QUESTIONS.items():
        lines.append(f"\n### {category}\n")
        for num, question in questions:
            q_key = f"Q{num}"
            answer = qa_pairs.get(q_key, f"[{question} - Not answered]")
            # Remove the "Q#:" prefix from the answer if present
            if answer.startswith(f"{q_key}:"):
                answer = answer[len(f"{q_key}:"):].strip()
            lines.append(f"**Q: {question}**\nA: {answer}\n")

    return '\n'.join(lines)


def get_full_question_list() -> Dict[str, List[tuple]]:
    """Get the full question list with categories."""
    return PERSONALITY_QUESTIONS
