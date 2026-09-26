# GPT-6 Astra Can Use Your Computer. This Changes Everything

- **Channel:** Vaibhav Sisinty
- **URL:** https://www.youtube.com/watch?v=yaLP3-1Rv8g
- **Category:** AI Systems
- **Processed:** 2026-09-12

## Summary
GPT-6 Astra transitions AI from passive conversational chatbots to autonomous agents capable of directly operating desktop software, physical hardware, and complex multi-step workflows.

## Key Takeaways
- Connect AI agents to real-world software and physical devices like Figma, Blender, iOS simulators, and robotic arms rather than restricting them to simple chat windows.
- Utilize a 'Research-First' prompt strategy by forcing the AI to analyze historical channel data, user metrics, or existing codebases before generating creative assets or building new features.
- Match the AI's effort level setting (Light, Medium, High, Extra High, Max, Ultra) to the specific difficulty and context length of the task to balance performance and consumption limits.
- Implement a 'Stop-and-Ask' rule in agent workflows so the system automatically pauses for human approval whenever money, sensitive permissions, or critical decisions are involved.
- Reverse-engineer existing complex digital products by having the AI conduct screen-by-screen web and mobile audits to produce detailed Product Requirements Documents (PRDs) and API blueprints prior to rebuilding.

## Actionable Frameworks
### Research-First Execution
A workflow methodology where the AI is tasked with analyzing existing assets, user data, or production code to create a formal research document/PRD before writing code or generating new assets.

### Stop-and-Ask Rule
A safety and control policy embedded into autonomous AI workflows that requires the agent to execute routine steps independently but stop and prompt the user for manual validation when reaching gated actions (payments, permissions, final publish).

## Memorable Quotes
> Astra becomes much more useful when you stop using it only to ask questions.

> You give Astra a goal, let it see what happened, and then allow it to improve the next attempt.

## Tags
`#ai` `#agents` `#automation` `#gpt-6` `#product management`

## Full Transcript

<details>
<summary>Click to expand full transcript (2,780 words)</summary>

I thought GPT6 Astra would just be another [music] smarter chatbot. Then I watched it use my computer for more than an hour without me touching anything. It opened apps, moved through software, and kept working until the task was done. So my team and I started testing how far we could actually take it. In this video, you'll see 10 things you can do with Astra, including connecting it to variables [music] and robots, building inside Figma and Blender, using your computer, and even studying an [music] entire product before helping you rebuild it.

While we were testing all of this, I kept seeing the same comments from you. I've shared a lot of prompts and resources on this channel. But many of you have been asking me to actually sit down and show you how to set this up properly. So, that's what we're doing. My team and I had Astra before it went public and we've spent that [music] time testing it on real work and finding out what it can and cannot handle. And people are already pushing it much further.

One developer gave it a week in Unreal Engine and rebuilt Manhattan Street by street. Another built a full city builder game with zoning and live police calls. In OpenAI's own demo, Astra opens Google Maps, finds a business, goes to its website, and fills out the form by itself. [music] So this weekend I'm running a live workshop where you'll build your own AI [music] employee with Astra from scratch. You'll choose its job, connect the tools it needs, set the permissions, link the steps it should follow, and add a stop [music] and ask rule so it comes back to you instead of guessing.

You'll build it with me live, and the goal is for you to leave with one running. Everyone who registers also gets the Astra power playbook with every prompt from this video written out. I'm keeping the first workshop small and registrations close in 24 hours. links in the description. Go register now. Now, let's get into the 10 things. The first example takes Astra outside the usual chat window. In this setup, a variable tracks how the back moves and sends that data into a 3D model of the body.

As the body moves, you can see those movements on the model and get a clearer idea of which muscles are working harder, which are working less, and where there may be extra strain. Normally, if your back hurts, you have to explain what you are feeling. With something like this, you can actually see the movement and understand it much more clearly. Instead of staring at rows of movement data, you get a visual model that makes the information much easier to understand. The second example applies the same idea to ankle movement.

Here, the ankle is connected to an interactive 3D anatomy model. As it moves, you can see what is happening around the joint and how that movement changes from one position to another. What would normally be hard to picture becomes much easier when you can see it in a 3D model. And this is where you should start thinking beyond a normal chat window. You can connect Astra to data tools and physical devices and use it for tasks that go far beyond simply answering questions. If you like practical experiments like these, subscribe to the channel because you will keep seeing what these models can actually help you do, not just how they score on benchmarks.

The third example takes this even further. Astra was connected to a camera and a robotic arm holding a paintbrush. The goal was to paint the Golden Gate Bridge. You can watch the attempts one after another. The first painting is rough. The next one gets better and then it improves again after Astra sees the previous result. You are not programming every tiny movement of the brush yourself. You give Astra a goal, let it see what happened and then allow it to improve the next attempt. These first three examples show you what becomes possible when Astras is connected to the physical world.

Now let's move into the workflows. You can actually try yourself. But before you start, choosing the right Astra mode is important. When you open GPT6 Astra, you will see light, medium, high, extra high, max, and ultra modes. For a simple task, light can be enough. If the task needs more planning or deeper thinking, high is usually a good place to start. If you are working on something with more context or several connected steps, you can move to extra high or max. Ultra is better suited to heavier coding and software work.

You do not need the highest mode every time. Choose it based on how difficult the task actually is. For this example, you can start with an old Airbnb investor deck. The information is fine, but the presentation itself looks basic. The layouts feel dated, the slides are plain, and the most important points do not stand out enough. Instead of redesigning every slide yourself, you can upload the original deck and ask Astra like, "Redesign this investor deck. Keep the content the same, but improve the layout, typography, colors, spacing, and hierarchy.

Add image 2.5 visuals where useful and export a polished PDF. Once you upload the file, Astra works through the deck, understands what each slide is trying to communicate, improves the layouts, creates new images where they are useful, and gives you a redesigned PDF. The information stays the same, but the final deck is much easier to follow and looks far more polished. You can use the same approach with a sales deck, proposal, report, college presentation, or any document where the content is good, but the design needs work.

For the next example, you can give Astra a normal photo and connect it to Figma. Instead of asking it to generate another image that simply looks like a painting, you can ask it to recreate this photo in Figma as a brush painting. Keep the same person pose, proportions, and composition. Build it from a blank canvas using individual strokes and include a replay. The final result uses 27,415 brush strokes. When you replay it, you can watch the portrait slowly appear from a black canvas. The face starts to form.

Then the clothes, lighting, and background come together until the full image is complete. You can also open the Figma file and inspect the finished result inside Figma itself. And that is what makes this useful. Astra is not just giving you an image at the end. It is actually doing the work inside software you already use. This is one of the easiest workflows to copy if you are a creator. If you ask AI to make a thumbnail with almost no context, the result will usually look generic.

It does not know what your audience clicks on, what your channel looks like, or which thumbnails have already worked well. So instead of asking Astra to design something immediately, you can first make it study your channel. Analyze my recent and top performing YouTube thumbnails. Find patterns in faces, composition, colors, copy, and visual style. Build a mood board. then create thumbnail directions for my GPT6 Astra video. The first result was already usable. Astra created a thumbnail with the copy GPT6 Astra tested. But the more interesting part is how it reached that result.

Astra reviewed around 130 thumbnails, selected the strongest references, found repeated patterns, and built an interactive mood board with several creative directions. Then you can push it further. Ask it to focus more on your top performing videos. create two stronger final options, improve the copy, and use official logos where needed. The final options included the end of prompting and GPT6 Astra. Can it do my job? So, if the result depends on your taste, your audience, or your past work, give Astra those references before you ask it to create anything.

Now, you can move from creating things to letting Astra use a computer. For this test, you can connect Astra to an iOS simulator and ask it using the iOS simulator, open Uber, and find rides from Apple Park to the Google Mountain View campus. Show me the available options and prices. Then you can simply watch it work. Astra opens Safari, goes to Uber, clicks through the website, enters the locations, waits for the available rides, and shows you the prices. You do not need to explain where every button is or tell it exactly what to click next.

You give it the result you want and it figures out how to get there. It stops at the list of rides because you have not told it which one to choose and that is exactly what you want. You can let Astra handle the repetitive steps while keeping the final decision for yourself whenever money permissions or anything important is involved. Next, you can connect Astra to Blender through MCP. The goal is to create a detailed 3D environment inspired by Winterfell from Game of Thrones. The easy prompt would be build Winterfell in Blender.

But if you start there, Astra has to guess too much about how the set should actually look. A better approach is to make it research the environment first. Astra goes through reference material, including YouTube videos of the set and creates a detailed research document first. Once the research looks right, you can tell it to follow that document and build the environment. Then you can open Blender and move around the result yourself. You can inspect the walls, courtyards, the famous tree, the surrounding forest, and different parts of the set.

You can even switch to wireframe view and see the 3D structure underneath. You can use the same process for a game environment, a film set, or any 3D project where the details matter. The more Astra understands before it starts building, the less it has to guess. The next example is not as flashy, but it can save you a lot of manual work. You can connect Astra to Google Sheets using the one-click plug-in, then give it access to the X and YouTube accounts you want it to organize.

The goal is to go through the profiles and channels you follow. Keep the ones related to AI and organize them into a useful directory. So, you can ask Astra to organize the AI related accounts I follow on X and YouTube in Google Sheets. Add the name, link, platform, category, subcategory, short description, and key details. Ignore unrelated profiles. Instead of creating one long list, Astra can build an AI directory, a category guide, and a coverage section. You can see the categories, subcategories, what each one means, and how many profiles are inside each group.

If useful information is spread across subscriptions, bookmarks, saved posts, or spreadsheets. This gives you a way to turn it into something you can actually search and use later. You can also connect Astra to Vid IQ and Metricool and let it study your actual channel data. Instead of asking it for random video ideas, you can give it your channel and ask it to find what is working right now. In this test, Astra reviewed 37 long form uploads, matched 36 of them with metricool data, looked at 75 uploads across three relevant channels, and read 78 comment threads.

From that research, it found three useful signals. Free tools get shared. challenge style videos can bring discovery and demand for GPT6 content was already high. Then it gave you 10 video ideas with titles, thumbnail directions, opening hooks, payoffs, story sequences, and the proof you would need inside each video. It also suggested what to publish first and built a 4-week publishing plan. It even set a practical target of 350,000 views within 28 days with 500,000 as the stretch goal and created a separate evidence CSV with the data behind its recommendations.

So instead of asking Astra what should I post next, you can give it your actual channel data and use it more like a YouTube consultant. This final example is the one you should pay the most attention to. Imagine you want to build an app similar to Spotify. The obvious prompt would be build me Spotify. But there is a problem. You are asking Astra to recreate a complicated product before it fully understands how that product works. So instead, you can make Astra study Spotify first like study the Spotify web and mobile apps screen by screen.

Map the main flows and interactions. Then create a detailed PRD and flowcharts that can be used as a blueprint to rebuild the product. A PRD is a product requirements document. You can think of it as a blueprint that explains the screens, features, user actions, rules, and how everything connects. Once the task starts, Astra asks which mobile platform you want it to focus on first. You can choose iOS if you want the iPhone version to be the priority. Then Astra opens the signedin Spotify web app and starts going through it.

It checks the login state, home, your library, settings, account, audio quality, display, and other parts of the product while mapping how everything works. It also asks what style you want for the final document. You can choose system design and Astra continues working through the product. Later, you can give Astra access to an actual phone through iPhone mirroring. Once you approve the permission and unlock the device, Astra can open the native Spotify iOS app and inspect the mobile experience as well. At that point, Astra is not relying only on what it already knows about Spotify.

It has actually gone through both the signedin web app and the native iOS app. The full task ran for around 1 hour and 13 minutes. At the end, you get a document called Spotify product research and rebuild requirements. Think of it as a complete research package you can use to rebuild the iOS version. It includes around 108 screen records, 176 interactions, 192 processed analytics events, and 18 flowcharts along with data models. It also includes API contracts, acceptance criteria, rebuild prompts, sign-in flows, screenshots, a feature priority list, and a web audit covering around 54 checkpoints.

Now, compare that with simply asking Astra to build Spotify. If you start with the build, Astra has to fill in too many gaps by itself. But if you make it study the product first, you can turn that research into a much clearer brief for the build. For something simple, you can give Astra a direct instruction. For something complicated, make sure it understands what you want to build before you ask it to recreate it. After these 10 examples, the main thing you should take away is that Astra becomes much more useful when you stop using it only to ask questions.

Start with the result you want. Then decide what information Astra needs, which tools it should have access to, and which decisions you still want to make yourself. That is why your presentation gets better when Astra has the original file. Your thumbnails get better after it studies your channel. And something like the Spotify project becomes much easier after Astra understands the product first. If you want to go beyond these examples and build your own AI employee with Astra, I am running the live workshop this weekend. You will build one from scratch, define its job, give it the right permissions, connect the steps it needs to complete, and add a stop and ask rule so it knows when to come back to

you instead of guessing. Everyone who registers also gets the Astra power playbook with every prompt from this video written out for you. Registrations close in 24 hours. So, use the link in the description if you want to join. Also, tell me in the comments which of these 10 ideas you want to see taken further. And if the Blender build in this video caught your attention, watch this video next. I tested Claude Fobble 5.1 on five practical builds, including a full 3D house in Blender from one prompt.

I'll put that video right here on the screen. Finally, around 70% of the people watching these videos are still not subscribed. So, if you want more practical AI tools, builds, prompts, and experiments like this, make sure you hit the subscribe button. See you in the next one.

</details>
