 � Growth Audit 
 GrowthLint v0.1.0                                                            
 Scanning: https://example.com                                                

  �� Fetched 528 bytes
  �� Platform: unknown
  �� Evaluated 31 rules
  �� Found 19 issues

 📊 Growth Score 
 48/100 (Grade: D)                                                            
 Critical: 2 | Warnings: 11 | Info: 6                                         
 24-57% potential conversion improvement                                      


# GrowthLint Audit Report

**Target:** https://example.com
**Date:** 2026-03-15 12:05
**Platform:** unknown
**Pages Scanned:** 1

---

## Growth Health Score

### � 48/100 (Grade: D)

**Revenue Impact:** 24-57% potential conversion improvement

| Severity | Count |
|----------|-------|
| Critical | 2 |
| Warning  | 11 |
| Info     | 6 |
| **Total** | **19** |

### Category Scores

| Category | Score |
|----------|-------|
| Analytics | �������������������� 78/100 |
| Attribution | �������������������� 90/100 |
| Conversion | �������������������� 89/100 |
| Seo | �������������������� 89/100 |

---

## Findings

### Critical Issues

####  No Analytics Tool Detected

> No analytics tool (GA4, Segment, PostHog, Mixpanel, etc.) was detected.

**Details:** No analytics tools detected

**Impact:** You're flying blind. Without analytics, you can't measure what's 
working, identify drop-offs, or make data-driven decisions.

**Fix:** Install an analytics tool. GA4 is free. For product analytics, consider
PostHog (open-source) or Mixpanel.

####  No Event Tracking Found

> Analytics is present but no custom event tracking was detected.

**Details:** No event tracking detected

**Impact:** Page views alone don't tell you what users do. Without event 
tracking, you can't measure CTA clicks, form submissions, or feature usage.

**Fix:** Add event tracking for key interactions: CTA clicks, form submissions, 
feature engagement, scroll depth.

### Warnings

####  CTAs Without Tracking Events

> Call-to-action buttons/links found but no click tracking events detected on 
them.

**Details:** Pattern 'addEventListener.*click|onclick|track.*click|click.*track'
not found in inline_scripts

**Impact:** If CTA clicks aren't tracked, you can't measure which CTAs perform 
best or optimize placement and copy.

**Fix:** Add click event tracking to all CTAs. Use data attributes or event 
listeners for clean tracking.

####  No Facebook/Meta Pixel

> No Facebook Pixel or Meta Pixel was detected.

**Details:** Pattern 'fbevents\.js|fbq\(|connect\.facebook\.net' not found in 
all_scripts

**Impact:** Without Meta Pixel, Facebook/Instagram ad retargeting is impossible 
and conversion attribution is lost.

**Fix:** Install Meta Pixel via GTM or direct snippet. Configure standard events
(PageView, Lead, Purchase).

####  No Google Ads Conversion Tag

> No Google Ads conversion tracking or remarketing tag was detected.

**Details:** Pattern 
'googleads\.g\.doubleclick|gtag.*AW-|google_conversion|googlesyndication' not 
found in all_scripts

**Impact:** Google Ads can't optimize bidding without conversion data. ROAS 
measurement is impossible.

**Fix:** Add Google Ads conversion tracking via gtag.js or GTM. Set up 
conversion actions in Google Ads.

####  UTM Parameters Not Persisted

> No client-side UTM parameter persistence logic was detected.

**Details:** Pattern 
'utm_source|utm_medium|utm_campaign|getParam.*utm|localStorage.*utm|cookie.*utm|
sessionStorage.*utm' not found in inline_scripts

**Impact:** UTM parameters are lost on internal navigation, breaking attribution
for multi-page journeys.

**Fix:** Store UTM parameters in localStorage/cookies on first page load. Pass 
them with form submissions and events.

####  High Form Friction (6+ Fields)

> Forms with more than 6 visible fields create friction.

**Details:** Found 0, expected at least 1

**Impact:** Each additional form field reduces conversions by 4-11%. Forms with 
6+ fields see 30-50% lower completion rates.

**Fix:** Reduce form fields to essentials (name, email, one qualifying field). 
Use progressive profiling for additional data.

####  No Social Proof Detected

> No customer counts, testimonials, reviews, or trust indicators found.

**Details:** No 'social_proof' elements found

**Impact:** 92% of consumers read online reviews before purchasing. Pages 
without social proof convert 15-30% lower.

**Fix:** Add customer testimonials, user counts, company logos, star ratings, or
case study references.

####  No Trust Signals Found

> No guarantees, security badges, or risk reducers detected.

**Details:** No 'trust_signals' elements found

**Impact:** Trust signals reduce purchase anxiety. Their absence increases cart 
abandonment by 17-20%.

**Fix:** Add money-back guarantee, free trial mention, 'cancel anytime', 
security badges, or compliance certifications.

####  Missing Meta Description

> No meta description tag was found.

**Details:** No 'description' elements found

**Impact:** Google shows a random snippet instead of your crafted message. 
Well-written descriptions increase CTR by 5-10%.

**Fix:** Add a compelling meta description (120-160 chars) with a value prop and
call to action.

####  Missing Canonical URL

> No canonical link tag was found.

**Details:** No 'canonical' elements found

**Impact:** Without canonical tags, search engines may index duplicate content 
or wrong URL variants, splitting page authority.

**Fix:** Add <link rel='canonical' href='https://yoursite.com/page'> pointing to
the preferred URL.

####  Missing Open Graph Tags

> No Open Graph (og:title, og:description) meta tags were found.

**Details:** No 'og_tags' elements found

**Impact:** Shared links on social media show generic previews instead of rich 
cards. Social CTR drops 30-50%.

**Fix:** Add og:title, og:description, og:image, and og:type meta tags for rich 
social sharing.

####  No Structured Data (JSON-LD)

> No JSON-LD structured data markup was found.

**Details:** No 'schema_markup' elements found

**Impact:** Structured data enables rich results (stars, FAQs, products) which 
increase CTR by 20-30% in search.

**Fix:** Add JSON-LD schema markup appropriate for your content type 
(Organization, Product, FAQ, Article, etc.).

### Info

####  No Error Tracking Detected

> No JavaScript error tracking (Sentry, Bugsnag, LogRocket, etc.) was found.

**Details:** Pattern 
'sentry|bugsnag|logrocket|rollbar|datadog.*rum|newrelic|errorhandler' not found 
in all_scripts

**Impact:** JavaScript errors silently break user flows. Without error tracking,
conversion-killing bugs go undetected.

**Fix:** Add error monitoring (Sentry is free tier, or use PostHog's error 
tracking).

####  No Google Tag Manager

> No Google Tag Manager container was detected.

**Details:** Pattern 'googletagmanager\.com/gtm\.js|GTM-[A-Z0-9]+' not found in 
all_scripts

**Impact:** Without GTM, adding new tracking requires code deploys. Marketing 
teams can't self-serve tag management.

**Fix:** Install GTM container. Migrate existing tags into GTM for centralized 
management.

####  No Referrer Source Tracking

> No document.referrer or traffic source capture logic detected.

**Details:** Pattern 
'document\.referrer|referrer|traffic.*source|first.*touch|last.*touch' not found
in inline_scripts

**Impact:** Without referrer tracking, you can't attribute conversions to 
organic, social, or referral channels.

**Fix:** Capture document.referrer on session start. Store first-touch and 
last-touch attribution data.

####  No Heading Hierarchy

> Page has H1 but no H2 subheadings to structure content.

**Details:** No 'h2' elements found

**Impact:** Content without structure is harder to scan. Users skim headings to 
find relevant info.

**Fix:** Add H2 subheadings that break content into scannable sections aligned 
with user questions.

####  No Visual Directional Cues

> No arrows, pointing imagery, or directional language detected near CTAs.

**Details:** Pattern '��|��|��|arrow|point|look|here|below|check.*out' not found in
text_content

**Impact:** Directional cues guide the eye toward CTAs, increasing click rates 
by 5-15%.

**Fix:** Add visual arrows, pointing imagery, or directional language near your 
primary CTA.

####  Missing Favicon

> No favicon link tag was found.

**Details:** No 'favicon' elements found

**Impact:** Missing favicons make your site look unprofessional in browser tabs 
and bookmarks. Minor trust signal.

**Fix:** Add a favicon: <link rel='icon' href='/favicon.ico'>. Use SVG for sharp
rendering at all sizes.

---

## Action Plan

**Priority fixes (do these first):**

1. **No Analytics Tool Detected** - Install an analytics tool. GA4 is free. For 
product analytics, consider PostHog (open-source) or Mixpanel.
2. **No Event Tracking Found** - Add event tracking for key interactions: CTA 
clicks, form submissions, feature engagement, scroll depth.
3. **CTAs Without Tracking Events** - Add click event tracking to all CTAs. Use 
data attributes or event listeners for clean tracking.
4. **No Facebook/Meta Pixel** - Install Meta Pixel via GTM or direct snippet. 
Configure standard events (PageView, Lead, Purchase).
5. **No Google Ads Conversion Tag** - Add Google Ads conversion tracking via 
gtag.js or GTM. Set up conversion actions in Google Ads.

---

*Generated by [GrowthLint](https://github.com/super0510/GrowthLint) - The 
ESLint for Growth Marketing*
