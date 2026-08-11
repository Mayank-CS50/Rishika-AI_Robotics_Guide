# Day 6 – Make Outbound Calls

Yesterday your agent waited to be called over the browser. Today, it will be making outbound calls.

For Day 6, your objective is to:

- **Step 1: Find the outbound use case for your track.**

  Examples of outbound use cases by track:

  | Track               | Call trigger                                                              |
  | ------------------- | ------------------------------------------------------------------------- |
  | Farm & Field        | Price crosses the seller's threshold; pest or rain warning for their crop |
  | Health Access       | Medication or vaccination reminder; follow-up after a triage escalation   |
  | Learning & Literacy | Daily practice call at a time the learner picked                          |
  | Local Commerce      | Order confirmation; restock nudge based on past order rhythm              |
  | Financial Services  | Scheme deadline approaching for someone already found eligible            |
  | Disaster Response   | Alert for a district; welfare check on a household flagged as vulnerable  |

- **Step 2: Integrate a Telephony Service.** Integrate a service like Twilio to your agent. See the [example project](https://github.com/murf-ai/murf-cookbook/tree/main/examples/agents/payment-reminder-agent) for reference.

- **Step 3: Have your agent call you**, or a number you control, and complete the interaction.

- **Step 4: Open the call properly.** Outbound is harder than inbound because the user didn't ask for this and doesn't know who you are. In the first two sentences: say who's calling, why, and how to make it stop.

- **Step 5: Record a short video** of the phone ringing and the call playing out.

- **Step 6: Post the video on LinkedIn** with a description of what you built on Day 6. Mention that you're building a voice agent using the fastest TTS API — **Murf Falcon**. Mention that you're part of **10 Days of Voice Agents** and don't forget to tag the official **Murf AI** handle. Also use the hashtag **#VoiceForBharat**.

- **Step 7: Submit your post link** on the submission form, along with your name and email.

## Advanced (Optional)

You only need the steps above to complete Day 6. These are for going the extra mile:

- **Outcome Handling**: Handle the outcomes inbound never has: no answer, busy, voicemail, and an immediate hang-up. Each needs a defined behaviour and a retry rule.

### You've finished Day 6 if:

- Your agent places a call and delivers something useful
- The opening states who is calling, why, and how to opt out

Once your agent is making calls, your LinkedIn post is live and your form submission is in, you've completed Day 6.

## Resources

- [Outbound Call Example Project Video](https://www.youtube.com/watch?v=qh0RoYac0No)
- [Outbound Call Example Project Code](https://github.com/murf-ai/murf-cookbook/tree/main/examples/agents/payment-reminder-agent)
- [Make Outbound Calls](https://docs.livekit.io/telephony/making-calls/outbound-calls/)
- [LiveKit Telephony](https://docs.livekit.io/telephony/)
- [LiveKit Agent Examples](https://github.com/livekit-examples/python-agents-examples)
