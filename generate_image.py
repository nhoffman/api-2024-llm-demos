from openai import OpenAI
client = OpenAI()

response = client.images.generate(
    model="dall-e-3",
    prompt="""A realistic painting of a cute robot in an orchard
    wearing a lab coat and safety glasses standing between two
    beautiful fruit trees. The tree on the right has low hanging
    branches with fruit that the robot can reach. The tree on the left
    is very tall and has fruit that is out of reach. It is looking up
    longingly at the fruit in the taller tree on the left and ignoring
    the fruit in the smaller tree that is clearly within reach. It is
    important that the two trees are not the same height.""",
    # prompt="""A realistic painting of a cute robot in a forest adorned
    # with a lab coat and safety glasses, positioned between two fruit
    # trees of contrasting heights. The tree to the robot’s right is
    # shorter with branches laden with easily reachable fruit. In stark
    # contrast, the tree on the left soars high, its fruit hanging far
    # out of reach. The robot, embodying a contemplative stance, gazes
    # up longingly at the towering tree’s unreachable fruit,
    # conspicuously disregarding the accessible bounty offered by its
    # diminutive counterpart. The distinct difference in the trees’
    # heights underscores the narrative of overlooked ease in favor of a
    # more challenging pursuit. Make sure that one of the trees is tall,
    # and the other is short with easily reachable fruit.""",
    size="1024x1024",
    quality="standard",
    n=1,
)

image_url = response.data[0].url
print(image_url)
