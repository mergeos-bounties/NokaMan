import json
import uuid
import os

cefrs = ["A1", "A2", "B1", "B2"]
topics = [
    "food", "travel", "hobbies", "school", "friends", 
    "technology", "sports", "shopping", "pets", "movies"
]

def make_sample(i):
    cefr = cefrs[i % 4]
    topic = topics[i % 10]
    
    text = f"This is a {cefr} text about {topic}."
    if cefr == "A1":
        text += f" I like {topic}. {topic.capitalize()} is good. I have many friends who like {topic}. We talk about {topic} every day."
    elif cefr == "A2":
        text += f" Recently, I have been thinking a lot about {topic}. It is very interesting to me. Last week I went to a {topic} event and it was great. I want to learn more about {topic} in the future."
    elif cefr == "B1":
        text += f" In modern society, {topic} plays a surprisingly significant role. Although some people might dismiss it as trivial, the impact of {topic} on our daily lives is undeniable. For instance, when we consider how much time and resources are devoted to {topic}, it becomes clear that it shapes our cultural landscape. Personally, I have found that engaging with {topic} has broadened my horizons and allowed me to connect with diverse groups of people."
    elif cefr == "B2":
        text += f" The multifaceted nature of {topic} presents a fascinating subject for sociological inquiry. While conventionally perceived as a straightforward domain, {topic} actually encompasses a complex web of economic, cultural, and psychological dimensions. Proponents argue that the proliferation of {topic}-related activities fosters community cohesion and individual self-actualization. Conversely, critics often point to the potential for commercialization and the superficiality that can sometimes accompany mass engagement with {topic}. Nevertheless, empirical evidence suggests that a balanced approach to {topic} can yield substantial benefits for both mental well-being and social capital."

    return {
        "id": f"en_reading_{topic}_{cefr.lower()}_{uuid.uuid4().hex[:6]}",
        "language": "en",
        "skill": "reading",
        "expected_cefr": cefr,
        "text": text
    }

for i in range(25):
    sample = make_sample(i)
    path = f"data/samples/{sample['id']}.json"
    with open(path, "w") as f:
        json.dump(sample, f, indent=2)

print("Generated 25 samples!")
