ALL: pdf

html:
	asciidoc memoria.asciidoc

pdf:
	a2x -f pdf -k \
	--dblatex-opts="-P toc.section.depth=2" \
	--dblatex-opts "-P latex.output.revhistory=0" \
	-a docinfo \
	memoria.asciidoc

epub:
	a2x -f epub -a docinfo memoria.asciidoc

clean:
	rm memoria.html
	rm memoria.pdf

