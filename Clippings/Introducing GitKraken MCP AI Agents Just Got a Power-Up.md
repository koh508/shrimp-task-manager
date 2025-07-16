---
title: "Introducing GitKraken MCP: AI Agents Just Got a Power-Up"
source: "https://www.gitkraken.com/blog/introducing-gitkraken-mcp"
author:
  - "[[Chris Griffing]]"
published: 2025-06-11
created: 2025-07-17
description: "With the latest iteration of the GitKraken CLI, you can now connect to a local MCP server to deliver more functionality to your agent of choice. Whether you"
tags:
  - "clippings"
---
![](https://www.gitkraken.com/wp-content/uploads/2025/06/MCP-Blog-Hero-1.png)

With the latest iteration of the GitKraken CLI, you can now connect to a local MCP server to deliver more functionality to your agent of choice. Whether you are using GitHub Copilot, Cursor, Windsurf, or any other tool, you can now leverage the power of GitKraken’s MCP server to enhance your workflows.

## TL;DR: Get Up and Running

1. Install the [GitKraken CLI](https://www.gitkraken.com/cli)
2. Run \`gk auth login\` to enable full functionality
3. Connect the MCP Server to your preferred tool (see examples in the [Help Center](https://help.gitkraken.com/cli/gk-cli-mcp/))
![](https://www.gitkraken.com/wp-content/uploads/2025/06/mcp-warp-1024x602.png)

VS Code

## What is MCP?

If you’re unclear on what MCP is and means, we can provide a bit of an introduction. MCP stands for Model Context Protocol and it’s a protocol that allows LLMs and AI tools to extend their capabilities. It’s a standard way of interacting with things like REST APIs, local CLI tools, web browsers, etc. Using GitKraken’s MCP server opens up a whole new world of possibilities for your agentic workflows.

## What Can You Do With It?

Would you like to ask Cursor questions about your codebase? Maybe you want to see who the subject matter expert is for specific code in your API or web app. Or maybe you want to list out all the open PRs and figure out which ones are most pressing for you to review.

The only limit to what you can do with the MCP server is your imagination. With the MCP server, your agent can now act like a real teammate by surfacing code insights, PR status, and team knowledge instantly.

![Screenshot of available MCP tools](https://www.gitkraken.com/wp-content/uploads/2025/06/tools-1024x693.png.webp)

Screenshot of available MCP tools

## Example Workflows

We have put together a few example workflows that you can use directly or treat as inspiration for your own custom workflows.

### Update Dependencies Across All Your Repositories

Let’s assume you have a common library you share across several of your repositories. In a previous role I had at another company, the backend team had dozens of AWS Lambda functions that shared an internal library of utilities and middleware. At least a couple times, they had to have Saturday merge “parties” when they had major updates to the shared library.

Now, they could simply prompt the LLM to update the dependencies in all of their repositories and even have it create the PRs for them.

Example Prompt:

> For all repositories in this GitKraken Workspace, create a new branch called “update-shared-components-to-X.X.X”, use npm to update the shared-component-library dependency to X.X.X and create Pull Requests for all affected repos. Make sure to tag “John Doe” as a reviewer.

### Learn About Your Codebase and Issues

If you have configured GitKraken Integrations, you could ask Cursor or other agentic tools to list issues that are assigned to you, or even look for the most pertinent issues in your backlog.

Another thing you could do is ask who has the most experience working with the auth layer of your API. This would help you reach out for any specific questions you might have as you look at the codebase.

Example Prompt:

> Look for all issues assigned to me in Jira. Find the most important one and then analyze the git commit history for the person I should reach out to if I have questions.

![](https://www.gitkraken.com/wp-content/uploads/2025/06/jira-issues-1024x636.png)

### Git branch Cleanup & maintenance

Do you ever manually delete branches from your local repo? I know I don’t. But that can get annoying when trying to autocomplete a branch name and you see branches from years ago still lingering in your options.

Ask Claude or Cursor to clean those branches up for you. Have them find branches that haven’t been updated in X days and ask for them to be deleted. You can have it do this for a single repo or you can have it do this across an entire workspace, saving you a lot of time. In the past, I would have wasted a bunch of time writing up a bash script for this. Now, it’s one prompt away.

Example Prompt:

> Look at all repositories in this GitKraken Workspace and find all local branches that have not been modified in 60 days. Show me the list along with their last modified dates.  
> (review the list)  
> Delete all those branches from my local git repository. Do not touch the remote branches.

## This is Just the Beginning

We are excited about the potential of this new MCP server and we are looking forward to seeing what you can do with it. If you have any questions or feedback, don’t hesitate to reach out to us. Tag @GitKraken on social media with interesting use cases or success stories!

- GitKraken CLI: [https://www.gitkraken.com/cli](https://www.gitkraken.com/cli)
- Help Center: [https://help.gitkraken.com/cli/cli-home](https://help.gitkraken.com/cli/cli-home)
- MCP-specific Help: [https://help.gitkraken.com/cli/gk-cli-mcp](https://help.gitkraken.com/cli/gk-cli-mcp)

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

[![](https://www.gitkraken.com/wp-content/uploads/2025/05/17.1-Hero-300x169.png)](https://www.gitkraken.com/blog/gitlens-17-1-visual-history-reimagined)

GitLens 17.0 delivers a transformative update that revolutionizes Git workflows directly within Visual Studio Code. Read more about the latest release here.

[Read More »](https://www.gitkraken.com/blog/gitlens-17-1-visual-history-reimagined)