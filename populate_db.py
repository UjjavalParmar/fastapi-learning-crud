import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import delete, select, update

import models
from database import AsyncSessionLocal, engine
from image_utils import PROFILE_PICS_DIR
from main import app

POPULATE_IMAGES_DIR = Path("populate_images")

USERS = [
    {
        "username": "UjjavalParmar",
        "email": "UjjavalParmar@gmail.com",
        "password": "DemoPass1!",
        "image": "Gemini_Generated_Image_17vmvh17vmvh17vm.png",
    },
    {
        "username": "MiraBuilds",
        "email": "mira@example.com",
        "password": "DemoPass2!",
        "image": "Gemini_Generated_Image_91eqo591eqo591eq.png",
    },
    {
        "username": "SamOnCall",
        "email": "sam@example.com",
        "password": "DemoPass3!",
        # No image - uses the default profile picture.
    },
    {
        "username": "NiaWritesCode",
        "email": "nia@example.com",
        "password": "DemoPass4!",
        # No image - uses the default profile picture.
    },
    {
        "username": "TheoMakesThings",
        "email": "theo@example.com",
        "password": "DemoPass5!",
        "image": "Media.jpeg",
    },
    {
        "username": "RaviLearns",
        "email": "ravi@example.com",
        "password": "DemoPass6!",
        # No image - uses the default profile picture.
    },
]

POSTS = [
    {
        "title": "The First Request Is a Tiny Production",
        "content": "My first API endpoint was one route and one response. It still had a client, a server, a contract, and a failure mode. Treating that small slice like a miniature production system helped me ask better questions: what comes in, what should go out, and what happens when the input is wrong?",
    },
    {
        "title": "Type Hints Are a Shared Map",
        "content": "A type hint is not a force field around a value at runtime. It is a useful map for editors, readers, and tools. In a FastAPI endpoint, those hints can also help the framework understand how to validate input and describe the API, which is why the same annotation can serve several jobs.",
    },
    {
        "title": "Schemas Are the Front Desk",
        "content": "The database model describes how information is stored. A request schema describes what a caller is allowed to hand us. A response schema describes what we choose to send back. Keeping those roles separate is like having a front desk check a form before it reaches the filing room.",
    },
    {
        "title": "Validation Is a Boundary, Not Decoration",
        "content": "A title that is too long or a password that is too short should be rejected before it becomes database state. Pydantic constraints make those rules visible beside the fields they protect. A good validation error tells the caller what to fix without exposing private internals.",
    },
    {
        "title": "What a Database Session Actually Does",
        "content": "I used to picture a session as the database itself. It is closer to a workbench for one unit of work: load records, make changes, commit them, or roll them back. The database is still a separate service or file underneath, and the session has to be closed when the work is done.",
    },
    {
        "title": "A Foreign Key Is a Promise",
        "content": "A post's user_id is not just a number that happens to match a user. A foreign key asks the database to enforce that relationship: the referenced user must exist. It is a small rule with a big payoff, because application code is not the only thing capable of making mistakes.",
    },
    {
        "title": "One User, Many Posts",
        "content": "The relationship is easier to see with two tables: one user can own many posts, while each post points back to one author. SQLAlchemy lets code walk that relationship, but the foreign key is what stores the connection. When I separate the Python convenience from the database fact, the model makes sense.",
    },
    {
        "title": "Dependency Injection Is a Request-Time Hand-Off",
        "content": "When a route asks for a database session with Depends, FastAPI arranges to provide one for that request. The route focuses on its job instead of constructing every helper itself. This is not a hidden global database connection; it is an explicit dependency with a lifecycle.",
    },
    {
        "title": "Async Means Yield While Waiting",
        "content": "An async endpoint does not make the CPU faster. It gives the program a chance to work on something else while this request waits for I/O, such as a database reply. If the code calls a blocking operation, the event loop can still get stuck. The mental picture is waiting efficiently, not doing everything at once.",
    },
    {
        "title": "The Useful Difference Between 401 and 403",
        "content": "A 401 response is about identity: the request has not proved who it is. A 403 is about permission: the server knows who is asking but that person cannot do this action. That distinction turns vague access errors into a much clearer map of the authorization flow.",
    },
    {
        "title": "A Password Should Never Come Back From the Database",
        "content": "The application needs to verify a password, not retrieve the original one. Store a slow password hash, then compare a login attempt against that hash. If a database copy leaks, hashing does not make the risk disappear, but it avoids handing attackers a neat list of reusable passwords.",
    },
    {
        "title": "JWTs Carry Identity, Not Permission by Themselves",
        "content": "A signed token can tell the server which user authenticated, and the signature helps detect tampering. That does not automatically mean the user may edit every record. The route still needs an authorization check for the specific resource and action.",
    },
    {
        "title": "The IDOR Bug Hides in a Missing Comparison",
        "content": "Imagine Alice changes a URL from /posts/12 to /posts/13 and sees Bob's private draft. The problem is not that IDs are easy to guess; the server failed to check ownership. Every request that reads or changes a protected object needs the right authorization rule.",
    },
    {
        "title": "Path or Query? Let the Resource Tell You",
        "content": "A path like /posts/42 names the particular post. A query like /posts?limit=10 asks for a shaped view of a collection. That is a useful rule of thumb, not a law of physics, but it keeps routes readable and predictable.",
    },
    {
        "title": "Pagination Is a Promise About Bounded Work",
        "content": "A list endpoint should not surprise its database or its caller with a million-row response. Limit and offset are simple to learn, and cursor pagination can be a better fit when lists change frequently. Either way, put a sensible upper bound on page size.",
    },
    {
        "title": "An ORM Query Still Has a Cost",
        "content": "SQLAlchemy makes database work feel like Python, but it still sends SQL to a database. A relationship load can quietly become many queries if used carelessly. I now ask two questions: what SQL does this produce, and how many times will it run?",
    },
    {
        "title": "Why Migrations Beat Recreating Tables",
        "content": "A schema change is a change to stored data, not just a line of Python. A migration records how to move from one database shape to another, so existing rows survive deployments. Creating tables from models is handy for a fresh learning database, but it is not a history of production changes.",
    },
    {
        "title": "A Transaction Is All-or-Nothing Work",
        "content": "Suppose an operation needs to update an account and record an audit event. If the first write succeeds and the second fails, partial state can be confusing. A transaction groups related database changes so they commit together or can be rolled back together.",
    },
    {
        "title": "A Useful Error Does Not Reveal Everything",
        "content": "Clients need to know whether an input was invalid or a resource was missing. They do not need a traceback, database URL, or secret in the response. Give callers a clear next step and send diagnostic detail to protected logs instead.",
    },
    {
        "title": "Logs Tell the Story Metrics Cannot",
        "content": "A latency graph can tell me that requests slowed down. A structured log with a request ID can help me trace one failing request through its steps. Metrics show patterns; logs add event detail. Neither is a substitute for the other.",
    },
    {
        "title": "Health Checks Need a Clear Question",
        "content": "A liveness check asks whether the process should be restarted. A readiness check asks whether it can handle traffic right now. Combining every dependency into one vague health endpoint can make an orchestrator restart a healthy process for a temporary database hiccup.",
    },
    {
        "title": "The Smallest Useful Rate Limit",
        "content": "A public endpoint can be correct and still be abused. Rate limiting puts a ceiling on how often a client can call it in a time window. Start with the endpoint that has a real cost or abuse risk, then choose a limit you can explain and observe.",
    },
    {
        "title": "CORS Is a Browser Rule, Not API Authentication",
        "content": "CORS tells browsers which web origins may read responses. It does not stop curl, a mobile app, or a server from calling the API, and it does not prove a caller is authorized. That distinction cleared up why a CORS setting cannot replace authentication.",
    },
    {
        "title": "When Background Tasks Are Enough",
        "content": "Sending a small email after a response can be a reasonable use for a framework background task. But work that must survive a process crash or be retried reliably usually needs a durable queue. The right tool depends on whether losing that work is acceptable.",
    },
    {
        "title": "Retries Need a Duplicate Plan",
        "content": "A timeout does not tell a client whether the server completed the operation. If the client retries a payment or job blindly, it might happen twice. Idempotency gives repeated requests a stable identity so the system can recognize work it has already done.",
    },
    {
        "title": "OpenAPI Is a Contract You Can Inspect",
        "content": "FastAPI's OpenAPI document describes routes, inputs, and responses in a format tools can read. That is useful for generated clients and interactive docs, but it only reflects what the application declares. A misleading schema is still misleading documentation.",
    },
    {
        "title": "A WebSocket Is a Conversation Left Open",
        "content": "A normal HTTP request usually ends with a response. A WebSocket connection stays open so both sides can keep sending messages. That is useful for live updates, but it also means managing connection lifetime, reconnects, and slow clients becomes part of the application.",
    },
    {
        "title": "Saturday's Sourdough Deployment",
        "content": "My starter has better uptime than some of my first side projects. It needs regular feeding, a warm environment, and a little patience. Bread is not software, of course, but the habit of checking conditions before changing a process has made both my kitchen experiments and my deployments calmer.",
    },
    {
        "title": "Custom Validation Should Protect a Real Rule",
        "content": "A custom validator is useful when a field's rule cannot be expressed as a simple type or length. Before writing one, I try to state the rule in a sentence and name the bad input it rejects. If I cannot describe that case, I may be adding cleverness without protection.",
    },
    {
        "title": "My Debugging Checklist for a Slow Route",
        "content": "First I reproduce one slow request and note its inputs. Then I separate time spent in the application from time waiting on the database or another service. A timer around every line is noisy; a few meaningful spans and a request ID make the path easier to understand.",
    },
    {
        "title": "A Container Is a Package, Not a Backup",
        "content": "An image can make application code and its runtime more repeatable across environments. It does not automatically protect the database, keep secrets safe, or make a deployment healthy. I think of the image as one deliverable in a release, not the whole release plan.",
    },
    {
        "title": "Configuration Should Fail Clearly",
        "content": "A missing production secret should stop startup with a clear message, not quietly fall back to a known default. Validating configuration early turns a mysterious authentication failure into an actionable deployment error.",
    },
    {
        "title": "A Good Test Names the Behavior",
        "content": "A test called 'test_update_post' tells me very little. 'A different user cannot edit this post' tells me the rule and the failure to guard against. Clear test names become a small map of what the application promises.",
    },
    {
        "title": "The Test Database Is Part of the Test",
        "content": "An API test that accidentally uses my local blog database is not isolated; it can change data I care about and pass for the wrong reasons. A separate test database and predictable fixtures make each run safer and easier to trust.",
    },
    {
        "title": "Tenant IDs Need a Trusted Source",
        "content": "In a shared SaaS database, filtering by organization_id is essential, but accepting that ID directly from a request does not prove membership. The server should derive the active organization from the authenticated user and verify access before reading or changing tenant data.",
    },
    {
        "title": "A Tenant Isolation Test Uses Two Accounts",
        "content": "Create one record for Acme and another for Northstar. Authenticate as an Acme member, then try to fetch Northstar's record. The expected denial proves more than a happy-path test: it checks the boundary that keeps one customer's data away from another.",
    },
    {
        "title": "The Modular Monolith Is a Real Architecture",
        "content": "Keeping one deployable application does not mean putting everything in one file. Clear modules can separate accounts, posts, and billing while keeping local calls simple. A modular monolith gives boundaries without making every request cross a network.",
    },
    {
        "title": "A Microservice Adds a Network Between Ideas",
        "content": "Splitting a module into a service changes more than the folder name. Calls can time out, requests can be duplicated, and deployments can disagree about a contract. I want a concrete ownership or scaling reason before adding those costs; 'microservices are modern' is not a reason.",
    },
    {
        "title": "A Request ID Makes a Log Trail",
        "content": "When a user reports a failed save, searching logs by timestamp alone is a guessing game. A request ID can travel with the request and its log messages, letting me follow one attempt through the service. It is a small operational detail with a very human payoff.",
    },
    {
        "title": "My Favorite Debugging Tool Is a Smaller Example",
        "content": "When a bug involves five users, three tables, and a background job, I reduce it to one user and one request. A tiny reproduction removes noise without changing the rule. Once that version makes sense, I add the missing complexity back one piece at a time.",
    },
    {
        "title": "A Feature Flag Is Not an Authorization Check",
        "content": "A feature flag can decide whether a capability is turned on for a rollout. It should not be the only thing stopping one user from reading another user's data. Rollout control and access control solve different problems and deserve different checks.",
    },
    {
        "title": "Build the Slow Path on Purpose",
        "content": "A user can lose a network connection after the server commits a change but before the response arrives. That awkward middle state is normal in distributed systems. Design the client and endpoint so retrying or checking the result does not turn uncertainty into duplicate work.",
    },
    {
        "title": "The Beginner's Advantage Is Asking What Happens Next",
        "content": "When I read a route now, I follow it line by line: what value enters, what check runs, what state changes, and what response leaves? That question works for authentication, database writes, and background tasks. It turns a wall of code into a sequence of causes and effects.",
    },
]

# Inserted first so the pagination example always has an oldest post.
POST_44 = {
    "title": "The Last Page Has a Note for the Curious",
    "content": "You made it to the oldest post in this little demo library. There is no secret prize, just a reminder that pagination is easier to understand when the records have dates and a stable order. Thanks for following the trail all the way back here.",
}


async def clear_existing_data() -> None:
    # Delete profile pictures from local storage
    if PROFILE_PICS_DIR.exists():
        for file in PROFILE_PICS_DIR.iterdir():
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()
        print(f"Deleted profile pictures from {PROFILE_PICS_DIR}")

    # Clear database tables (order respects foreign keys)
    async with AsyncSessionLocal() as db:
        await db.execute(delete(models.PasswordResetToken))
        await db.execute(delete(models.Post))
        await db.execute(delete(models.User))
        await db.commit()
    print("Cleared existing data")


async def update_post_dates() -> None:
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Post).order_by(models.Post.id))
        posts = result.scalars().all()

        if not posts:
            return

        # First post (POST_44) is the oldest - ~90 days ago
        await db.execute(
            update(models.Post)
            .where(models.Post.id == posts[0].id)
            .values(date_posted=now - timedelta(days=90)),
        )

        # Remaining posts: each ~1.5 days newer than previous
        for i, post in enumerate(posts[1:], start=1):
            days_ago = (len(posts) - i) * 1.5
            hours_offset = (i * 7) % 24
            post_date = now - timedelta(days=days_ago, hours=hours_offset)
            await db.execute(
                update(models.Post)
                .where(models.Post.id == post.id)
                .values(date_posted=post_date),
            )

        await db.commit()
    print("Updated post dates")


async def populate() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://localhost",
    ) as client:
        # Clear existing data (local images first, then database)
        await clear_existing_data()

        users: list[dict] = []

        print(f"\nCreating {len(USERS)} users...")
        for user_data in USERS:
            response = await client.post(
                "/api/users",
                json={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            user = response.json()
            print(f"  Created: {user['username']}")

            response = await client.post(
                "/api/users/token",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            token = response.json()["access_token"]

            if image_name := user_data.get("image"):
                image_path = POPULATE_IMAGES_DIR / image_name
                if image_path.exists():
                    response = await client.patch(
                        f"/api/users/{user['id']}/picture",
                        files={
                            "file": (
                                image_name,
                                image_path.read_bytes(),
                                "image/png",
                            ),
                        },
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    response.raise_for_status()
                    print(f"    Uploaded: {image_name}")

            users.append(
                {"id": user["id"], "username": user["username"], "token": token},
            )

        print(f"\nCreating {len(POSTS) + 1} posts...")

        # First create POST_44 (will become oldest after date update)
        response = await client.post(
            "/api/posts",
            json={"title": POST_44["title"], "content": POST_44["content"]},
            headers={"Authorization": f"Bearer {users[0]['token']}"},
        )
        response.raise_for_status()
        print(f"  Created: '{POST_44['title']}'")

        # Create remaining posts in reverse (last in list = oldest, first = newest)
        for i, post_data in enumerate(reversed(POSTS)):
            user = users[i % len(users)]
            response = await client.post(
                "/api/posts",
                json={
                    "title": post_data["title"],
                    "content": post_data["content"],
                },
                headers={"Authorization": f"Bearer {user['token']}"},
            )
            response.raise_for_status()
            title = post_data["title"]
            print(
                f"  Created: '{title[:50]}...'"
                if len(title) > 50
                else f"  Created: '{title}'",
            )

        print("\nUpdating post dates...")
        await update_post_dates()

    await engine.dispose()

    print("\nDone!")
    print(f"  {len(USERS)} users")
    print(f"  {len(POSTS) + 1} posts")
    print("  Profile pictures saved locally")


if __name__ == "__main__":
    asyncio.run(populate())
