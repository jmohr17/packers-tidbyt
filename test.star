load("render.star", "render")

def main():
	return render.Root(
		child=render.Text(
			"GO PACK GO",
			color="FFB612",
		),
	)
