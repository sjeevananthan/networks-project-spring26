## Methodology Notes

RTTs were measured using Python's `urllib` with 15 probes per target and a 0.2s delay between probes.
Two categories of targets were used: Google country-code TLDs (e.g. `google.co.jp`) and institutional
university servers (e.g. `tohoku.ac.jp`). These targets both behaved differently. Google targets are served by
nearby CDN edge nodes regardless of the destination country, so their RTTs reflect edge proximity
rather than true end-to-end paths. University servers respond from their actual physical location,
making them better indicators of geographic routing but more prone to server-side variability.

São Paulo (`google.com.br`) was unreachable across all runs and networks.

## Question 1 — Highest Inefficiency Ratio

Seoul (snu.ac.kr) had the highest inefficiency ratio at ~40x across multiple runs.

On [submarinecablemap.com](https://submarinecablemap.com), the cables serving South Korea include
EAC-C2C, AJC, TPE, and APCN-2, most of which land on Korea's west coast and connect
westward through Japan or southward through Southeast Asia before reaching transpacific cables to
the US West Coast. Traffic from Burlington (US East Coast) must first cross the continent to a
West Coast interconnect point, then traverse a transpacific cable, then route through intermediate
hops in Japan or Hong Kong before reaching Seoul's network. This added thousands of kilometers of
detour on top of the already large geographic distance.

Additionally, `snu.ac.kr` is a university server with no CDN acceleration, meaning the request
hits the actual origin server in Seoul rather than a nearby cache, compounding the latency.

## Question 2 — Closest to Theoretical Minimum

Sydney (`google.com.au`) achieved a ratio of ~1.57x, the closest to the theoretical minimum.

This is primarily a CDN effect — Google serves Australian requests from edge infrastructure
that is well-connected to US East Coast peering points via transpacific cables such as
Southern Cross NEXT and Hawaiki. The low ratio reflects highly optimized routing with
minimal queuing or detour, not necessarily that Sydney itself has exceptional infrastructure.

Singapore (`google.com.sg`) was similarly close at ~1.64x for the same reason. Both results
suggest that Google's transpacific cable investments have produced near-optimal paths between
the US East Coast and the Asia-Pacific region.

## Question 3 — Why Lagos Routes Through Europe

The packet to Lagos almost certainly travels: Burlington → transatlantic cable → European hub
(London or Lisbon) → submarine cable down the African west coast → Lagos.

This routing exists for historical and economic reasons. Most submarine cables serving West Africa, 
including SAT-3/SAFE, WACS (West Africa Cable System), and ACE (Africa Coast to Europe), were built
and funded by European telecommunications companies and are designed to connect African
coastal cities to European internet exchange points, not directly to North America. As a result,
even US-to-Africa traffic gets routed eastward across the Atlantic to Europe first, then back
south along the African coast, adding roughly 10,000+ km of unnecessary path.

To fix this, two things would need to change:
1. Direct US-Africa submarine cables: cables like the proposed BELLA (Brazil and Europe Link
   for Latin America) and newer initiatives would create direct transatlantic paths bypassing Europe.
2. African IXPs (Internet Exchange Points): more regional exchange infrastructure within Africa
   would allow traffic destined for Lagos to terminate locally rather than tromboning through
   European hubs. Currently, much intra-African traffic also routes through Europe, which compounds
   the inefficiency for any packet entering the continent.


