## Kasada protection
I found great article on Kasada bypass, and it doesn't seem too complicated. There are many enthusiasts that are kind enough to share their knowledge and work with others.
https://hackernoon.com/kasada-anti-bot-bypass-techniques-save-money-with-these-open-source-solutions

And looks like most of the problems are already solved. I'll try patchright and camoufox solutions. 
I did some research on Kasada, it has several mechanisms to prevent bot spam. I will work on each of these (some is done by default):
- [ ]
- [x] Client validation
Checks data integrity, done by default since we use legit browser client.
- [ ] Anomalies in user interactions. There goes:
  - [ ] Mouse movements - solved by creating approximation movement function from a to b. It is a simple math and probably have been solved by dozens of people.
  - [ ] Click timings - again, solved by others
  - [x] Scrolling patterns - No scrolling will be performed.
  - [ ] Key presses and timings. We don't need anything but ctrl+v combination. Probably will use some kind of library anyway.

Even though it is stated on Kasada page and have been researched by individuals that this tracking exists I couldn't prove it myself in the source files. So I'll implement user interactions only if they are proven to be necessary.

- [ ] Fingerprinting:
  - [ ] IP reputation - we'll rotate tor network IPs for different viewers, if possible. It is best to use many residential IPs, but I don't have access to that.
  - [x] TLS fingerprinting - we'll use chrome suit for playwright, TLS will be natural
  - [ ] HTTP headers - need deeper research
  - [ ] Hardwawre/Browser/OS details - not sure if we can fake it if client js collects this data. We'll fake it in headers though.
- [ ] Analysis of use behaviour over time. Well, I have no idea whether I can fake this one. It might be more benefitial to simply print out more accounts than to solve this one.

- [ ] Kick collects telemetry in logs. Damn these guys make it hard. It might be that without session logs and session itself bots will be banned soon. I may consider faking it, but there are a lot of things to gather info from to do that. Hope everything will work without this point.

If combination of these approaches is not enough then the only solution is to use payed API to get around Kasada wall. I consider this solution as defeat.
