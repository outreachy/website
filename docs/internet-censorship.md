# Internet Censorship Preparation Guide

## Overview
Internet censorship occurs when access to certain websites, applications, or online services is restricted by governments, internet service providers (ISPs), or organizations. 

For Outreachy interns, this can disrupt access to essential tools such as code repositories, communication platforms, and documentation resources. This guide provides practical strategies to help interns detect, prepare for, and work around such restrictions while staying safe.

---

## What Gets Blocked
During internet censorship, the following resources are commonly restricted:

- Code hosting platforms (e.g., GitHub, GitLab)
- Communication tools (e.g., Slack, Discord, email services)
- Social media platforms (e.g., Twitter, Facebook, WhatsApp, Telegram)
- Video and learning platforms (e.g., YouTube)
- App stores (e.g., Google Play Store, Apple App Store)
- Privacy and security tools (e.g., VPN websites, Tor Project website)

The extent and type of censorship vary depending on the country and situation.

---

## Detecting Censorship
It is important to identify whether an issue is due to censorship or a general network problem. The following methods can help:

- Use tools like **OONI Probe** to test whether websites or services are blocked
- Check **OONI Explorer** for global, real-time censorship data
- Look for common browser errors such as:
  - "Connection timed out"
  - "Access denied"
  - "DNS resolution failed"
- Compare access using different networks (e.g., mobile data vs Wi-Fi)
- Use DNS or network testing tools to detect interference

These methods help confirm whether access restrictions are intentional.

---

## Circumventing Restrictions
Some tools and techniques can help bypass internet censorship:

- **VPNs (Virtual Private Networks)**  
  Encrypt your internet traffic and route it through servers in other locations  
  Examples: ProtonVPN, Psiphon

- **Tor Browser**  
  Routes your traffic through multiple relays to provide anonymity and bypass restrictions

- **Tor Bridges**  
  Special relays that are harder to detect and block by censorship systems

- **Tails OS**  
  A portable operating system that routes all internet traffic through the Tor network

Note: The use of these tools may be restricted or illegal in some regions. Always understand local regulations before using them.

---

## Preparing in Advance
Preparation is essential to continue working during internet restrictions:

- Install multiple VPN applications in advance
- Download and set up Tor Browser (including bridge configuration if needed)
- Clone important repositories locally using `git clone`
- Download offline documentation using tools like Zeal or Dash
- Save important guides and tutorials as PDFs
- Keep backups of essential files on external storage devices (USB drives)

Being prepared ensures minimal disruption to your work.

---

## Working Offline
If internet access becomes limited or unavailable:

- Continue working using locally cloned repositories
- Write and edit code offline
- Use offline documentation tools such as Zeal
- Maintain notes and track changes to sync later
- Prepare commits locally and push them once internet access is restored

Offline workflows help maintain productivity during outages.

---

## Risks and Safety
Circumventing censorship can involve legal and personal risks depending on your location.

Interns should:
- Be aware of local laws regarding VPNs and privacy tools
- Avoid sharing sensitive personal or project-related information
- Use secure and trusted tools only
- Understand the risks before attempting to bypass restrictions

Safety and legal awareness should always be the top priority.