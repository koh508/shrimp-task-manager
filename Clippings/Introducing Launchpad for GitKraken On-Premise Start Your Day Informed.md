---
title: "Introducing Launchpad for GitKraken On-Premise: Start Your Day Informed"
source: "https://www.gitkraken.com/blog/introducing-launchpad-for-gitkraken-on-premise"
author:
  - "[[Jonathan Silva]]"
published: 2025-03-13
created: 2025-07-17
description: "GitKraken On-Premise customers, we’ve got exciting news! The powerful Launchpad feature, previously available only in GitKraken Cloud, is now making its way to your self-hosted environment. This update brings a simplified, efficient, and fully local way to start your day informed—helping you stay on top of your Git activity without relying on external cloud services."
tags:
  - "clippings"
---
![GitKraken logo with subtitle of "Launchpad for On-Premise"](https://www.gitkraken.com/wp-content/uploads/2025/03/gitkraken-launchpad.png)

GitKraken On-Premise customers, we’ve got exciting news! The powerful Launchpad feature, previously available only in GitKraken Cloud, is now making its way to your self-hosted environment. This update brings a simplified, efficient, and fully local way to start your day informed—helping you stay on top of your Git activity without relying on external cloud services. ![A screenshot of GitKraken Desktop On-Premise with the Launchpad screen open](https://www.gitkraken.com/wp-content/uploads/2025/03/launchpad-1024x640.png) Let’s dive into what’s new, what’s different, and how Launchpad enhances your workflow while respecting your on-premise setup.

#### What is Launchpad for On-Premise?

Launchpad serves as your personal Git activity hub, giving you an at-a-glance view of your repositories, pull requests, and issues—all pulled directly from your connected Git provider. ![A screenshot of the Launchpad with the issues tab selected. The screen displays issues tied to the repos ](https://www.gitkraken.com/wp-content/uploads/2025/03/on-prem-launchpad-issues-1024x444.png)

With the on-premise version, we’ve optimized the experience by removing all cloud dependencies, ensuring that your data stays local and secure.

Key Features:

- View issues and pull requests assigned to or mentioning you
- Filter your activity based on project, provider, or status
- Seamless integration with on-prem Git providers (e.g. GitHub Enterprise, GitLab Self-Managed)
- No internet connection required—everything runs within your local environment

#### What’s Different from the Cloud Version?

Since GitKraken On-Premise is designed to function without sending data outside your network, we’ve streamlined Launchpad to fit this use case. Here’s what’s changed:

- No Cloud Workspaces – In the cloud version, workspaces help teams organize repositories across providers. The on-premise version focuses solely on your personal repositories and activity from your connected Git provider.
- No Snoozing or Pinning – Since these features require cloud storage, they’ve been removed from the on-prem version.
- No Team Launchpad – Because Cloud Workspaces are not available, Team Launchpad remains cloud-only.
- Filtering Still Works – You can still filter issues and PRs by assignment, mention, and status, just like in the cloud version.
- View Settings – While you can’t save Views, you can still toggle view settings and the app will remember your preferences.

#### How It Works

Using Launchpad in GitKraken On-Premise is simple:

Open GitKraken On-Premise and navigate to the Launchpad (you’ll find it via the shortcut button in the upper-left corner).

![A cropped screenshot of GitKraken Desktop UI with the rocket icon highlighted, and arrow icon pointing to it](https://www.gitkraken.com/wp-content/uploads/2025/03/open-launchpad.png)

Click on rocket icon in upper left corner to open Launchpad

Select your Git provider (such as GitHub Enterprise Server).

![](https://www.gitkraken.com/wp-content/uploads/2025/03/launchpad-select-provider-1024x516.png)

Choose an integration

View all relevant **issues and pull requests** connected to your user.

![](https://www.gitkraken.com/wp-content/uploads/2025/03/launchpad-prs-1024x557.png)

Use the available filters to focus on what matters most. sure everything’s up to date.  
![](https://www.gitkraken.com/wp-content/uploads/2025/03/launchpad-filter.png)

Since this is a fully local experience, no data leaves your network, making it ideal for teams with strict security and compliance requirements.

To see the Launchpad in action, watch our tutorial video below.

[![](https://www.gitkraken.com/wp-content/uploads/2025/03/Invite-Teams-1024x576.png)](https://youtu.be/orph3qwVjO4)

## Stop Merge Conflicts Before They Happen—With Some Key Differences

There’s more to the 10.8 release!

Merge conflicts can slow down your workflow at the worst possible moment, but with **GitKraken’s Conflict Prevention**, you don’t have to wait until you open a pull request to discover a problem. GitKraken Desktop proactively warns you about potential conflicts **before they happen**, giving you the chance to fix them early and keep your development process smooth.

### What’s Available for On-Prem Users?

Since On-Prem customers operate without cloud connectivity, some conflict prevention features are different from the cloud version. Here’s what’s available:

Get alerts for conflicts with your target branch – GitKraken will compare your local branch against its remote target branch (e.g., main or develop) and let you know if there’s a conflict. This helps you avoid merge surprises and clean up issues early.

![In GitKraken Desktop, clicking a target icon warning expands to show details about a potential merge conflict. The menu lists the conflicted branches and provides options to rebase, merge, stop detecting conflicts for target branch, or set target branch settings.](https://www.gitkraken.com/wp-content/uploads/2025/03/non-org-conflict-menu-1024x502.png)

Take action on potential conflicts

##### What’s Not Available in On-Prem?

Because GitKraken On-Premise **does not send local changes to a backend for comparison**, it **cannot**:

- Detect conflicts with another contributor’s branch
- Show overlapping changes with GitKraken Org members
- Send a Cloud Patch to preview changes before merging
- Invite non-Org members to collaborate on changes

**Bottom Line:** If you’re using On-Prem, **conflict detection only works between your branch and its remote target branch**. You won’t get alerts about potential conflicts with teammates working on separate branches like you would in GitKraken Cloud.

## Multi-Commit Cherry Pick: A Better Way to Move Code

Ever needed to move multiple commits from one branch to another? Cherry-picking is a powerful way to do that—but doing it commit by commit can be tedious and error-prone. That’s why GitKraken gives you the ability to **cherry-pick multiple commits at once**, making it easier than ever to move code efficiently.

![](https://www.gitkraken.com/wp-content/uploads/2025/03/multi-cherry-pick-menu-1024x510.png)

Use the shift or ctrl key to multi-select commits in the Commit Graph. Then right-click to access cherry pick

Selecting the option to cherry pick multiple commits opens an interactive cherry pick tool that allows you to reorder (with drag and drop of mouse), squash, reword, or drop any of the commits selected.

![](https://www.gitkraken.com/wp-content/uploads/2025/03/interactive-cherry-pick-1024x576.png)

Choose whether to pick, squash, reword, reorder, or drop commits

### What Makes Multi-Commit Cherry Pick So Powerful?

**Select multiple commits at once** – No need to repeat the process for each commit.  
**Preview changes before applying** – Know exactly what will be moved before committing.  
**Works across branches seamlessly** – Move code between branches with confidence.

This feature is especially useful when you need to:

Apply bug fixes to multiple branches  
Move feature development from one branch to another  
Backport important changes without merging unnecessary commits

By integrating multi-commit cherry-picking into your workflow, **you save time, reduce mistakes, and stay in control of your Git history**.

## What’s Next?

Our team is actively working on refining the on-premise experience based on customer feedback. If you have questions or suggestions, we’d love to hear them! Additionally, we’re updating our **GitKraken Help Center** with more details about this feature, so stay tuned.

For now, if you’re an On-Premise customer, **[update to the latest version of GitKraken](https://help.gitkraken.com/gitkraken-desktop/upgrade-enterprise/#elementor-toc__heading-anchor-1) and try out Launchpad today!**

Got questions? Drop us a line at [GitKraken Support](https://help.gitkraken.com/gitkraken-desktop/contact-support/?product_s_=GitKraken%20Desktop), and let us know what you think!

[![](https://www.gitkraken.com/wp-content/uploads/2025/07/Group-19756-1-300x195.png)](https://www.gitkraken.com/blog/get-ready-gitkraken-ai-all-access-week-starts-july-8)

July 8–11 is officially GitKraken’s first official All Access Week, we’re unlocking all of our Advanced features for free and we’re taking all the limits off of GitKraken AI.

[Read More »](https://www.gitkraken.com/blog/get-ready-gitkraken-ai-all-access-week-starts-july-8)

[![](https://www.gitkraken.com/wp-content/uploads/2025/06/zoomvideo-syd-300x168.gif)](https://www.gitkraken.com/blog/gitkraken-is-a-great-place-to-work-three-years-running-%f0%9f%90%99%e2%9c%a8)

GitKraken is certified as a Great Place To Work for the second consecutive year! Want to join this amazing team of Krakeneers?

[Read More »](https://www.gitkraken.com/blog/gitkraken-is-a-great-place-to-work-three-years-running-%f0%9f%90%99%e2%9c%a8)

[![](https://www.gitkraken.com/wp-content/uploads/2025/06/Blog-Hero-New-300x169.png)](https://www.gitkraken.com/blog/gitlens-17-2-commit-composer-streamlined-ux-and-enterprise-controls)

GitLens 17.0 delivers a transformative update that revolutionizes Git workflows directly within Visual Studio Code. Read more about the latest release here.

[Read More »](https://www.gitkraken.com/blog/gitlens-17-2-commit-composer-streamlined-ux-and-enterprise-controls)

[![](https://www.gitkraken.com/wp-content/uploads/2025/06/GKD-11.2-Thumb-5-300x169.png)](https://www.gitkraken.com/blog/gitkraken-desktop-11-2-merge-conflicts-meet-ai-and-more-dev-quality-of-life-wins)

We’ve been steadily building something powerful into GitKraken: AI that understands your code and your context. In recent releases, GitKraken AI has already helped you:

[Read More »](https://www.gitkraken.com/blog/gitkraken-desktop-11-2-merge-conflicts-meet-ai-and-more-dev-quality-of-life-wins)

[![](https://www.gitkraken.com/wp-content/uploads/2025/06/Bday-Blog-HERO-300x169.png)](https://www.gitkraken.com/blog/celebrating-a-decade-of-gitkraken)

As I sit down to write this, I can’t help but feel a wave of nostalgia wash over me. I’m Sara Stamas, VP of Marketing

[Read More »](https://www.gitkraken.com/blog/celebrating-a-decade-of-gitkraken)

[![](https://www.gitkraken.com/wp-content/uploads/2025/06/MCP-Blog-Hero-1-300x169.png)](https://www.gitkraken.com/blog/introducing-gitkraken-mcp)

With the latest iteration of the GitKraken CLI, you can now connect to a local MCP server to deliver more functionality to your agent of

[Read More »](https://www.gitkraken.com/blog/introducing-gitkraken-mcp)