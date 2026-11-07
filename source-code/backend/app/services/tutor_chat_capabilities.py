"""Read-only capability truth shared by help replies and the tool UI."""
from app.errors import DomainError
from app.services.assessment_access import TutorCapability, require_tutor_access


def available(db, settings, principal, session):
    from app.services import assessments, tutor_past_papers, tutor_sources
    def gate(capability,workflow):
        try:
            require_tutor_access(db,settings,principal.user.id,capability,session.subject_id,
                                 workflow,topic_id=session.active_topic_id)
            return True
        except DomainError as error:
            if error.status_code not in {403,409}: raise
            return False
    practice=False
    if not settings.tutor_text_pilot and gate(TutorCapability.TOOLS,'tutor_practice'):
        try:
            practice=any(session.active_topic_id in row[2] for row in assessments.eligible_questions(db,principal.user.id,session.subject_id))
        except DomainError as error:
            if error.status_code not in {403,409}: raise
    voice=gate(TutorCapability.VOICE,'tutor_voice')
    # Do not advertise a credential path if no published focus source exists.
    if voice:
        focus,version,_=tutor_sources._active_chunks(db,session)
        voice=bool(version)
        if settings.tutor_release_gates_required:
            from app.services.evaluations import tutor_feature_allowed
            voice=tutor_feature_allowed(db,session.subject_id,'tutor_voice',settings.tutor_realtime_model,'1.0.0')[0]
        if voice:
            from app.services.tutor_quotas import available_voice_seconds
            voice=available_voice_seconds(db,principal.user.id)>0
    papers=False
    try:
        tutor_past_papers.require_access(db,settings,principal,session)
        papers=bool(tutor_past_papers.eligible(db,principal.user.id,session.subject_id))
    except DomainError as error:
        if error.status_code not in {403,409}: raise
    return {'guidedPractice':practice,'voice':voice,
            'recommendations':gate(TutorCapability.TOOLS,'tutor_next_topic'),
            'pastPapers':papers,'automaticMarking':False}


def help_response(db,settings,principal,session,kind):
    from app.services import tutor_sessions
    from app.models import TextbookTopic
    choice=next((s for s in tutor_sessions.options(db,principal.user.id,settings).subjects if s.id==session.subject_id),None)
    topics=choice.topics if choice else []
    subject=choice.name if choice else session.subject_id.title()
    capabilities=available(db,settings,principal,session)
    if kind=='topics':
        content=f'Here are the published, covered {subject} topics released for you:\n\n'+ '\n'.join(f'- {t.groupCode} · {t.code} · {t.title}' for t in topics)
        if session.chat_scope=='topic':
            content+='\n\nThis is a Topic chat. Use Move topic to choose another available topic; I will not switch it automatically.'
        choices=['How can you help me with this subject?']
    else:
        content=f'I can help you study {subject}:\n\n- Explain concepts using your approved textbook material and references.\n- Ask revision questions and help you reason through an idea.\n- Show relevant approved figures when available; I do not generate images.'
        if session.chat_scope=='subject': content+='\n- Connect ideas across the published, covered topics released for you.'
        if capabilities['pastPapers']: content+='\n- Practise released past-paper questions and compare your answer with approved marking guidance. Automatic scores have separate review and release requirements.'
        if capabilities['guidedPractice']: content+='\n- Open an eligible saved guided-practice question using the practice tools.'
        if capabilities['voice']: content+='\n- Use the voice tools, subject to your microphone permission and remaining allowance.'
        if capabilities['recommendations']: content+='\n- Use Find next topic for evidence-based guidance; I will say when there are not enough assessed results to personalise it.'
        content+='\n\nAsk me to explain a concept, quiz you, or list the available topics. What would you like to work on?'
        active=db.get(TextbookTopic,session.active_topic_id)
        focus=next((t for t in topics if active and t.topicRef == active.public_ref), topics[0] if topics else None)
        choices=['Which topics can we study?'] + ([f'Ask me three questions about {focus.title}'] if focus else [])
    if not topics: content='No published, covered topics are currently released for this session. Ask your administrator to check enrolment, coverage and content release.';choices=[]
    return content,choices,capabilities
