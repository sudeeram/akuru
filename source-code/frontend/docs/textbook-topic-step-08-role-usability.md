# Step 8 — Role-specific usability and accessibility

The portal retains its horizontal top navigation and AKURU BOT loading transition on every role. A visible-on-focus skip link sends keyboard users directly to the page content.

## Admin

The **Textbook structure** workspace provides a labelled catalogue search plus subject and content-status filters. Search includes textbook, Unit or Module, and topic fields without showing internal references. The selected textbook remains a normal labelled control. Each group and topic has explicit **Earlier** and **Later** controls, so ordering does not rely on drag-and-drop. Action groups have screen-reader names.

**Grade & term coverage** has a labelled term filter. It filters the planning view only; the plan still explains that learner access accumulates prior terms. Unit or Module wording is taken from the selected textbook configuration.

Publishing, archiving and removal have confirmation only where the action changes published or removes content. Routine saves, filtering, editing and ordering do not interrupt the workflow.

## Students and parents

Existing topic-progress cards show the configured group label, topic title, score, confidence and evidence count. Statuses use a visible symbol and clear text so colour is never the sole indicator. This works at tablet widths because filter panels and action rows reflow into a single column.

## Shared accessibility behaviour

Controls have labels, native controls remain keyboard operable, focus rings apply to buttons, links, inputs, text areas and comboboxes, and count updates use a polite live region. The design honours reduced-motion preference for loading transitions.
