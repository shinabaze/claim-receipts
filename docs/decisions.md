# Decisions

Short reasons for the choices that look odd at first.

**No proof means no receipt, and the claim is marked unverified.** A weak receipt is worse than
none: it tells the reader the claim was checked when it wasn't. Refusing is the default answer,
and every refusal says why.

**Words count only in the number's own window.** A page about one topic has many numbers and many
of our words. Without the window, any page with the number somewhere and our words somewhere else
passes. That is how the first version accepted three false receipts.

**The smallest block that holds the number decides.** In a row of stat cards the row's text is
"26% More Weekend Rides 41% Higher Bus Ridership...", and the window behind a number reaches back
into the card before it. Judging each card on its own stops a neighbour lending its words.

**The named source needs less evidence.** On the source's own page, the number beside one of our
specific words is strong evidence. On a stranger's page the same number may be a coincidence, so it
takes twice as much.

**Round numbers need a specific word.** 41% or 50% turns up everywhere. Matching one beside only
generic words ("rate", "total") would prove almost anything.

**The highlight is CSS over the image, never painted in.** The screenshot stays an exact copy of
what the page showed, and the marks are percentages, so they stay on the words at any width.

**Fixed and sticky elements are hidden before the crop.** Cookie bars and sticky headers otherwise
land on top of the passage, and the receipt shows a banner instead of the sentence.

**Crude stemming is enough.** The word lists are short and the test is overlap, not meaning. A full
stemmer would add a dependency and change little. Plurals are cut (trips, buses) and that is it.

**The matcher has no dependencies; the browser is optional.** The rules are the part worth testing
and reusing, so they run on saved HTML with the standard library. Playwright is only needed to take
the screenshot.
