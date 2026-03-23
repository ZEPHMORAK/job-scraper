function createAuditForm() {
  var form = FormApp.create('Business Systems Audit');

  form.setDescription(
    'A short audit to understand how your business operates — where information flows, ' +
    'where decisions are made, and where the biggest opportunities for improvement are. ' +
    'All answers are confidential. Takes 5–10 minutes.'
  );
  form.setCollectEmail(false);
  form.setProgressBar(true);

  // ── 1. BUSINESS MODEL ──────────────────────────────────────────────────────
  form.addSectionHeaderItem()
    .setTitle('Business Model');

  form.addCheckboxItem()
    .setTitle('What are your core services?')
    .setChoiceValues(['Property verification', 'Legal documentation', 'Property sales'])
    .showOtherOption(true)
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('Who are your main clients?')
    .setChoiceValues(['Individuals', 'Diaspora clients', 'Property developers', 'Corporations'])
    .showOtherOption(true)
    .setRequired(true);

  // ── 2. CLIENT ACQUISITION ──────────────────────────────────────────────────
  form.addPageBreakItem()
    .setTitle('Client Acquisition');

  form.addCheckboxItem()
    .setTitle('How do clients currently find you?')
    .setChoiceValues(['Referrals', 'Social media', 'Property agents', 'Website', 'Walk-ins'])
    .showOtherOption(true)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('How do you handle new inquiries?')
    .setChoiceValues(['WhatsApp', 'Phone calls', 'Email', 'All of the above'])
    .showOtherOption(true)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('How fast do you typically respond to a new inquiry?')
    .setChoiceValues(['Within 1 hour', 'Same day', '1–2 days', 'Longer than 2 days'])
    .setRequired(true);

  // ── 3. OPERATIONS ──────────────────────────────────────────────────────────
  form.addPageBreakItem()
    .setTitle('Operations');

  form.addParagraphTextItem()
    .setTitle('Walk us through your full process — from client request to final delivery.')
    .setHelpText('List the key steps in order.')
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('What tools does your team currently use to manage work?')
    .setChoiceValues(['Microsoft Word / Excel', 'Paper files', 'Email', 'WhatsApp', 'Google Drive'])
    .showOtherOption(true)
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Which part of the process takes the most time — and why?')
    .setRequired(true);

  // ── 4. DOCUMENTS ───────────────────────────────────────────────────────────
  form.addPageBreakItem()
    .setTitle('Documentation');

  form.addMultipleChoiceItem()
    .setTitle('How do you currently store client documents?')
    .setChoiceValues(['Physical files only', 'Google Drive / cloud', 'Email attachments', 'Dedicated software'])
    .showOtherOption(true)
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Have you ever lost or misplaced an important document?')
    .setChoiceValues(['Yes, more than once', 'Once or twice', 'Never'])
    .setRequired(true);

  // ── 5. COMMUNICATION ───────────────────────────────────────────────────────
  form.addPageBreakItem()
    .setTitle('Communication & Follow-up');

  form.addMultipleChoiceItem()
    .setTitle('Do clients frequently ask for status updates on their case?')
    .setChoiceValues(['Yes, very often', 'Sometimes', 'Rarely'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Have you ever forgotten to follow up with a client?')
    .setChoiceValues(['Yes, it happens', 'Rarely', 'Never'])
    .setRequired(true);

  // ── 6. RISKS & BOTTLENECKS ─────────────────────────────────────────────────
  form.addPageBreakItem()
    .setTitle('Risks & Bottlenecks');

  form.addParagraphTextItem()
    .setTitle('What is the biggest operational problem in your business right now?')
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('If you could fix ONE thing in your operations immediately — what would it be?')
    .setRequired(true);

  // ── DONE ───────────────────────────────────────────────────────────────────
  var url = form.getPublishedUrl();
  Logger.log('✅ Form created!');
  Logger.log('📋 Client URL: ' + url);
  Logger.log('✏️  Your edit URL: ' + form.getEditUrl());
}
