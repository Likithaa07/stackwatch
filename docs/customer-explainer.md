# How your Splunk stack was sized, and how to read StackWatch

## How we chose your stack size
1. **You told us your needs:** how much data you send per day, how long you keep it, how many people search,
   and which premium apps you use (for example Enterprise Security).
2. **SizeRight turned that into servers.** Each indexer can handle a set amount of data per day, and less when
   searches are heavy or premium apps are running (300 GB light, 200 GB moderate, 150 GB heavy, 100 GB with
   Enterprise Security). Your daily data divided by that number gives your indexer count; search heads,
   storage and high availability are added on top.
3. **Your planned capacity** = indexers x GB per indexer. This is the number StackWatch checks against.
   Every plan records which version of the sizing rules was used, so a change in the rules is visible.

## How we check it is still right
Your stack sends usage every minute. StackWatch divides **what you actually use** by **what we planned**:

| Status | Meaning | What we do |
|---|---|---|
| **OK** (green) | between 40% and 90% of planned capacity | nothing; this is the healthy range |
| **UNDERSIZED** (red) | above 90% for 15+ minutes; searches and data may slow down | we are alerted and re-size with you |
| **OVERSIZED** (yellow) | below 40% for 60+ minutes; you are paying for unused capacity | we suggest a smaller stack |
| **NO DATA** (grey) | nothing received for 10+ minutes | we check our pipeline first, then contact you |

## Reading the dashboard
- **Status table:** one row per stack, coloured as above. Click a row to see only that stack.
- **Utilisation chart:** your usage over time. The red dashed line is 90%, the yellow one 40%; staying between
  them is healthy. Daily ups and downs are normal; a steady climb towards the red line means growth.
- **Rules check:** "ok" means your plan uses today's sizing rules; "MISMATCH" means it is due a refresh.

## What you will hear from us
- **Incidents** (alerts) are acted on within minutes, using a written runbook.
- **Every week** you get a short report ranking stacks by how far they are from the healthy range, each with
  one recommended action. Peak-hour usage drives re-sizing advice, so a stack can be OK today and still be
  flagged for growth.
