# 9. User guide

[Documentation home](README.md) · Previous: [8. Platform architecture](08-platform-architecture.md) · Next: [10. Developer guide](10-developer-guide.md)

**Open the platform:** <https://ete-platform.streamlit.app> (add `?lang=en` for English or `?lang=fr` for French).
**Weak connection?** Use the light page: <https://ezequiasmiocha.github.io/ete-platform/>.

The platform has five pages, read from top to bottom, plus a page for each place and an account page. It works on a
computer and on a phone. The screenshots below are the English version on 22-24 November 2026, a quiet green period;
in a flood season the same places show yellow, orange or red.

> **The free host puts the application to sleep** when nobody visits it for a while. If you see "Your app is waking
> up", wait a minute. The light page never sleeps.

## The parts you see on every page

![Top of the home page](figures/platform/home_top.jpg)

1. **The top line** (purple): the date of the bulletin and until when it is valid, a button to get alerts on
   WhatsApp, share buttons, and the language switch **PT | EN | FR**.
2. **The menu**: Home, Water quality, Floods, Alerts, The project, and **Sign in** (optional account).
3. **The search bar**: type the name of your neighbourhood or village (for example *Machubo* or *Macaneta*) to open the
   page of that place, or a few words of a question (for example *drink*, *radar*, *alerts*) to jump to the section that
   answers it.
   Accents and small typos do not matter.
4. **The footer**: contacts for technical questions, the disclaimer, the link to the light page, the supporters and the
   open-data credits.

## Home

The home page answers the two questions of the project in the first screen.

- **The greeting** gives today's level in one sentence (*"No sign of flooding on the Incomati"*), the level card
  (green, yellow, orange or red, with the date it is valid until) and **what to do today**.
- **How is the river water?** One sentence about the colour of the water at Manhiça, Marracuene and the mouth, the
  satellite photograph next to the colour map (drag the white bar), the five-step colour scale, the forecast for the
  next four weeks and the most important advice for families.

![Home: the river water](figures/platform/home_water.jpg)

- **Will the river flood in the coming days?** Move from day to day with the arrows: each day shows its level, the
  forecast flow and the probability of crossing each limit.

![Home: the next days](figures/platform/home_floods.jpg)

- **Two doors**: get the alerts on your phone, or learn what the project is. Below them, three **curiosities** about
  the river and the satellites, which change every day.

![Home: doors](figures/platform/home_doors.jpg)

## Water quality

![Water quality: today](figures/platform/water_today.jpg)

**Today.** The latest clear Sentinel-2 image of the river, from just north of Marracuene to the mouth, with one
sentence per section (*"In Marracuene, the water is much muddier than usual"*). The colour scale has five steps, from
*very clear* to *very muddy*, compared with ten years of images of the same stretch; grey means no reading (clouds,
shadows, plants, the pixel next to the bank). Switch on *Interactive map* for a zoomable map (it uses more data), or
open *The river from Manhiça (full map)*.

**What to do with the water.** Choose your group: families, farmers and livestock keepers, fishers, schools, health
facilities, those who treat and supply water, or authorities and community leaders. Each card says what the situation
means, what to do, and what the data show. *Download this advice to share* gives a text file for WhatsApp. Below:
*How to treat water at home* in six steps, and *Diarrhoea: what to do*.

![Water quality: advice](figures/platform/water_advice.jpg)

**The water in the coming weeks.** Choose a week: the map shows the forecast colour of the river and the chart the
most likely colour at Marracuene morning by morning; the grey band is where 8 days out of 10 fell in the tests. The panel *The next
days, morning by morning* gives the probability of water more turbid than usual for the next mornings in three
reaches. Read it as a guide, not a certainty.

![Water quality: the coming weeks](figures/platform/water_coming_weeks.jpg)

**The water in past years.** Choose a year (arrows) and a month: the map shows the colour of the river in that month
and the chart compares the same month in every year since 2017, with this year's forecast.

![Water quality: past years](figures/platform/water_past_years.jpg)

**The whole river, from the border to the mouth.** The nine sections Q1 to Q9, each compared with the same season in
other years (*normal*, *high*, *very high*, or no recent measurement). Open the panels for a table and a map, each
section month by month since 2006, and the months that strayed from normal.

![Water quality: the whole river](figures/platform/water_whole_river.jpg)

**How we measure.** Five cards on the method, what the satellite sees and does not see, and a link to the models and
their tests.

![Water quality: how we measure](figures/platform/water_how_we_measure.jpg)

## Floods

**The next ten days.** The bulletin sentence, the level of each day (the colour bar under each day) and the forecast
flow at Marracuene: the line is the middle scenario, the light band the range from the lowest to the highest likely
value of the 51 scenarios. The text under the chart says how far the river is from each limit. Panels give the forecast
day by day in a table and the rain in the basin.

![Floods: the next ten days](figures/platform/floods_ten_days.jpg)

**What each colour means**, and what to do at each level:

![Floods: what each colour means](figures/platform/floods_colour_meanings.jpg)

**Where the water arrives first.** The two warning zones from the January 2026 flood. Choose a place in *Find a place*
to see it on the map; the panel *All the places, in the order they flood* lists every named place.

![Floods: where the water arrives first](figures/platform/floods_where_water_arrives.jpg)

**The river seen from space.** On the left, the real photographs of 23 October 2025 and 24 January 2026 (drag the
white bar). On the right, the radar map of any month since 2016 (arrows to change month): blue is the usual water, red
is flood water. The radar sees through clouds; in built-up areas it can mark flood where there is none.

![Floods: the river seen from space](figures/platform/floods_from_space.jpg)

**Twenty years of the river.** How many days a year the alert rules would have warned since 2006, the highest flow,
and panels with one year in detail, the flow and rain of the last three years, and the flooded area month by month.

![Floods: twenty years](figures/platform/floods_twenty_years.jpg)

## The page of a place

Type a place in the search bar (or choose it in *Find a place*) to open its page, for example
<https://ete-platform.streamlit.app/?p=zona&lugar=Machubo&lang=en>. It gathers everything about that place:

- three answers at the top: **flooding in the next 10 days?**, **how is the river water?** (nearest section),
  **can I drink the river water?**;
- **Floods: what to expect here**: the 10 days, what the January 2026 flood did there (first map with water, share of
  the 500 m circle that flooded, buildings within 500 m, distance to the river, height above the river) and a picture
  of the warning zones around it;
- **The river flow** forecast and **the river water near you** with its advice;
- **Your area seen from space**: a 6 km square before and during the flood (radar where clouds covered the photograph),
  with a 500 m circle around the place;
- **Get the alerts for this place** and **Share on WhatsApp**, a direct link for people who live there.

![The page of a place](figures/platform/place_page_top.jpg)

![A place seen from space](figures/platform/place_page_from_space.jpg)

Place names come from OpenStreetMap and GeoNames and are not yet confirmed on the ground. Each place is a point with a
500 m circle, not an official neighbourhood boundary.

## Alerts

Sign up with your WhatsApp number, your place and your full name; sex, age group and occupation are optional and only
used to choose the advice. Choose the language of the messages and accept the terms. You receive a welcome message at
once; after that, a message only when the alert for your area is orange or red, and again when the danger has passed.
*Stop receiving* removes your number.

![Alerts: sign up](figures/platform/alerts_sign_up.jpg)

**Today's message for community leaders** is a short text, updated every day, to forward by WhatsApp or SMS to
people without internet. It is written to fit in an SMS and stays in Portuguese, the language of the communities.

![Alerts: message for community leaders](figures/platform/alerts_community_leaders.jpg)

> **Status.** Sending WhatsApp messages needs an approved WhatsApp Business account and a hosted database. Until both
> are set up, the published form says that sign-ups open soon. The leaders' message works today.

## The project

Objectives, the problem, who it is for, how it works, how far to trust it, frequently asked questions, the machine
learning models with their tests, where each piece of information comes from, a glossary, the state of the system
today, the supporters and the contacts.

![The project page](figures/platform/project_top.jpg)

![How it works](figures/platform/project_how_it_works.jpg)

![How far to trust it](figures/platform/project_trust.jpg)

![The machine learning models](figures/platform/project_models.jpg)

## Account (optional)

An account remembers your name, your place and your alerts; everything else stays open to everyone without an
account. Your password is never stored, only a fingerprint of it that nobody can read. Keep the recovery code shown
when you create the account: it is the only way to reset a forgotten password.

![Account](figures/platform/account.jpg)

Like WhatsApp sign-ups, accounts need the hosted database; until then the published platform hides the *Sign in*
button.

## On a phone

On screens up to 700 px the page becomes a single column, with a slim top line (bulletin date and language) and a fixed
bar at the bottom: Home, Water, Floods, Alerts, Project. Pictures and cards are sized for a 360-400 px screen.

![Phone views](figures/platform/phone_views.jpg)

## Frequently asked questions

**The alert is green, but it is raining hard here.** The alert is about the Incomati, whose water comes mostly from
far upstream, in South Africa and Eswatini. Heavy local rain can flood streets and fields without the river rising.
Follow the local authorities.

**How many days of warning does it give?** In January 2026 the rules turned orange five days before flood water was
first mapped at Marracuene. Every flood is different; the forecast looks 10 days ahead.

**Can I trust the flow number?** It comes from a global model (GloFAS), not from a gauge in the river. Use it as an
order of magnitude and look at the level, which compares the forecast with 25 years of the same model.

**The water is "normal". Can I drink it?** Not without treating it. The satellite sees mud, not germs or chemicals.
Boil it (a rolling boil for at least one minute) or use chlorine at the dose on the bottle and wait 30 minutes.

**What does "forecast unavailable" mean?** That today's data could not be fetched or did not pass the checks, or that
the bulletin is more than 36 hours old. The platform never shows green in that case: follow the official warnings.

**My neighbourhood does not appear.** The list holds the 84 places named on open maps. Choose the nearest one, or tell
us through the contacts in the footer.

**Does this replace the warnings of INGD, INAM and ARA-Sul?** No. It is an experimental service that complements them.
If the authorities give an order, follow the order.
