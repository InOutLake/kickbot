## Conclusion
This phase marks the end of my deep dive into Kasada’s bot-defense system (kpsdk). Over many hours of request analysis, traffic inspection, and research, I achieved partial automation of the login flow using Patchright—a promising step forward. However, persistent challenges remain:

IP rotation is still required to avoid rate-limiting or flagging,
My domain was banned after deploying an email automation API (a humbling reminder that infrastructure alone isn’t enough).
While I didn’t fully reverse-engineer or bypass Kasada’s protections (a task demanding deeper expertise—or time I’m choosing to invest elsewhere), the existence of third-party solvers confirms it’s feasible, just not yet efficient for this project’s scope.

For now, I’m pivoting pragmatically:
- Using a small pool of manually registered accounts for stability,
- Optionally integrating a paid registration proxy service and email accounts for scalability—without burning domains or IPs.

## Next steps
With defense research paused (for now), I’m shifting focus to building the core system.

