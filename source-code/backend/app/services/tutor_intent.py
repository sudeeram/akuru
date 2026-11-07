"""Zero-model-call teaching approach selection; specialised tools retain priority."""
import re

VERSION='teaching-intent-v1.1'


def select_approach(message, subject, history=()):
    value=message.strip().lower()
    if re.search(r"\b(?:don['’]?t|do not|stop)\s+(?:quiz|test|ask)\b|\bexplain\b.*\b(?:directly|simply)\b|\bmore direct\b",value):
        return 'explanation','explicit_explanation'
    if re.search(r'\b(?:without (?:telling|giving|showing)|don[\'’]?t (?:tell|give|show).{0,25}answer|work it out myself|socratic)\b',value):
        return 'socratic_practice','reason_without_reveal'
    if re.search(r'\b(?:six|[1-9]|\d+)\s*[- ]?marks?\b|\b(?:exam technique|structure (?:my|an?) answer|command words?)\b',value):
        return 'exam_technique','exam_answer_technique'
    if subject=='french' and re.search(r'\b(?:convers|pronunci|speak|speaking|vocabulary|order.{0,12}food|parlons|bonjour)\w*',value):
        return 'french_conversation','french_language_activity'
    if re.search(r'\b(?:revise|revision|recap|summari[sz]e|test tomorrow|exam tomorrow)\b',value):
        return 'revision','revision_request'
    if re.search(r"\b(?:stuck|struggling|help me solve|guide me|step by step|don['’]?t understand.{0,30}question)\b",value):
        return 'guided_practice','staged_help'
    if re.search(r'\b(?:quiz me|test me|ask me|ask.{0,18}questions?|give.{0,18}questions?)\b',value):
        return 'questions','recall_request'
    if re.fullmatch(r'(?:another one|next one|another question|one more|continue)[.!? ]*',value):
        for turn in reversed(history):
            if turn.role=='assistant':
                mode=(getattr(turn,'response_data',{}) or {}).get('teachingMode')
                if mode in {'questions','guided_practice','socratic_practice','revision','french_conversation'} and (mode!='french_conversation' or subject=='french'):
                    return mode,'own_session_continuation'
                break
    return 'explanation','default_explanation'


def help_kind(message):
    v=re.sub(r'\s+',' ',message.strip().lower().strip('\"“”‘’')).rstrip('?.! ')
    v=re.sub(r'^please\s+','',v)
    v=re.sub(r'^tell me (?=(?:what|which|how)\b)','',v)
    v=re.sub(r'\s*,?\s+please$','',v)
    # Strip polite wrappers only around an actual capability/topic question.
    # A request such as 'tell me about cells' must retain factual grounding.
    v=re.sub(r'^(?:can|could|would) you (?:please )?(?:tell me|explain|show me) (?=(?:what|which|how)\b)','',v)
    subject=r'(?:this (?:subject|topic|course)|(?:the )?(?:biology|chemistry|physics|maths|mathematics|french|ict|english|human biology)(?: (?:subject|course))?)'
    if re.fullmatch(r'(?:what (?:(?:can|could|will) you|you (?:can|could|will)) teach(?: me)?|what (?:(?:can|could|will) i|i (?:can|could|will)) (?:learn|study)|what (?:(?:will|do|can) we|we (?:will|can)) (?:learn|study|cover)|(?:what|which) (?:topics|units|chapters)(?: and (?:topics|units|chapters))? can you (?:teach|cover)(?: me)?)(?: (?:on|in|about|for) '+subject+r'| here)?',v):
        return 'overview'
    # Anchored to capability questions; mixed/factual questions are not swallowed.
    if re.fullmatch(r'(?:what (?:topics|units|chapters) (?:are available|can (?:we|i) (?:study|learn|cover))|which (?:topics|units|chapters) (?:are available|can (?:we|i) (?:study|learn|cover)))(?: (?:here|in (?:this subject|biology|chemistry)))?',v):
        return 'topics'
    if re.fullmatch(r'(?:how can you help(?: me)?|what can (?:you|i) do(?: here)?|how (?:do|can) i use (?:this tutor|akuru|this chat)|what (?:help|support) (?:can you offer|is available))(?: (?:with|in|for) (?:this (?:subject|topic)|biology|chemistry|physics|maths|french|ict|english|human biology))?',v):
        return 'capabilities'
    return None
