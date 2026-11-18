# Scoring without model calls

Some reviewed questions use exact numeric, multiple-choice or labelled-answer rules. These can be tested and marked without paid AI calls. Other questions still need semantic or manual marking.

## Admin

In a question's scoring panel, inspect the recognition rules and source evidence. Rule changes require a new source assessment and a new **Validate without model calls** run. Review expected and actual marks, credited points, referred answers and whether the saved certificate is current. A developer can perform these operations through authenticated APIs; repeating them in the browser is unnecessary.

A certificate establishes scoring readiness only. Content approval, curriculum, reviewed visuals and Tutor release remain separate gates. Never make an unsupported explanation automatic merely because its extraction confidence is high.

## Student

Enter the final answer in the supplied field. For a labelled question, use each matching label. Where offered, enter arithmetic working one expression per line. If AKURU cannot reliably recognise the response, it saves it for review without guessing a mark or treating it as a wrong answer. No paid AI fallback runs automatically.
