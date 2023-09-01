## 🤗 Welcome

:+1::tada: First off, We are really glad you're reading this, because we need volunteer developers to help improve the Field Mapping Tasking Manager (FMTM)! :tada::+1:

We welcome and encourage contributors of all skill levels, and we are committed to making sure your participation is inclusive, enjoyable, and rewarding. If you have never contributed to an open source project before, we are a good place to start, and we will make sure you are supported every step of the way. If you have **any** questions, please ask!

You can see an overview of the project and the process we have gone through in developing FMTM so far in these [slides](https://docs.google.com/presentation/d/1UrBG1X4MXwVd8Ps498FDlAYvesIailjjPPJfR_B4SUs/edit#slide=id.g15c1f409958_0_0) .

Furthermore, there are many ways to contribute to the **Field Mapping Tasking Manager (FMTM)**, which includes:

## Testing

Right now, we are in the process of building the prototype. We warmly welcome your input in testing and sharing your feedback. If you are also interested in coordinating a field testing session, please reach out!

## Code contributions

Create pull requests (PRs) for changes that you think are needed. We would really appreciate your help!

In fact, we are specifically looking for input from developers with **Python skills** and **familiarity with Fast API**.

## Report bugs and suggest improvements

The [issue queue](https://github.com/hotosm/fmtm/issues) is the best way to get started. There are issue templates for BUGs and FEATURES that you can use, you could also create your own. Once you have submitted an issue, it will be assigned one label from the following [label categories](https://github.com/hotosm/fmtm/labels). If you are wondering where to start, you can filter by the **good first issue label**.

## :handshake: Thank you

Thank you very much in advance for your contributions!! Please ensure you refer to our **Code of Conduct**.
If you've read the guidelines, but are still not sure how to contribute on Github, please reach out to us via our Slack **#geospatial-tech-and-innovation**.

# Code Contribution guidelines

## Workflow

We operate the "Fork & Pull" model explained at [About Pull
Requests](https://help.github.com/articles/about-pull-requests/)

You should fork the project into your own repo, create a topic branch
there and then make one or more pull requests back to the repository.
Your pull requests will then be reviewed and discussed by other
developers. Don't submit a Pull Request while still developing the
code, wait till the feature is complete and ready for review. A
preliminary review by other developers can be requested via the
comments for the issue on github, or via slack or email.

It is prefered that all patches contain any documentation
updates made, and for any new features, a test case is preferred when
possible. Keep patches focused on a single feature to avoid merging
complications with other developers. The old free software joke is
"patches are better than bug reports" is how we contribute to the
community of people involved with this project.

# If you are reporting a problem

- Describe exactly what you were trying to achieve, what you did, what you
  expected to happen and what did happen instead. Include relevant information
  about the platform, OS version etc. you are using. Include shell commands you
  typed in, log files, errors messages etc.

- Please open a separate issue for each problem, question, or comment you have.
  Do not re-use existing issues for other topics, even if they are similar. This
  keeps issues small and manageable and makes it much easier to follow through
  and make sure each problem is taken care of.

## Documentation

Project documentation should be in [Markdown
format](https://www.markdownguide.org/), and in a _docs_
subdirectory. While it is possible to use HTML in Markdown documents
for tables and images, it is prefered to use the Markdown style as
it's much easier to read.

## Coding Style

Python enforces a certain amount of style due to indent levels. Unlike
C/C++, we don't have to worry about curly braces. It is prefered that
all code follows object oriented techniques, with a minimal amount of
code other than basic control in the main function. This allows code
to be easily reused and run either standalone, or part of a REST API
backend. Code that is not designed to be run standalone can have a
main function to do simple testing during development. That test code
should be moved to a standalone test case when possible.
[Pytest](https://pytest.org/) is used as the test framework for
standalone test cases.

Code follows a [CamelCase](https://en.wikipedia.org/wiki/Camel_case)
style. Classes use an Upper Case for the first word, method use a
lower case for the first word. Variable names are all lower case with
an underbar as a word separator. Properly naming everything makes it
much easier to read the code and get an idea of what it is doing. This
enables people new to this project to contribute easier.

All methods should have a comment that can be used by
[pydoc](https://docs.python.org/3/library/pydoc.html). The usage of
base classes is encouraged so functionality can be shared. Comments in
the code are encouraged when necessary to explain code that may not be
obvious, but avoid over commenting as well. Code should be able to be
read like a book, with descriptive names used, no fancy tricks unless
required. Always be concious of performance and security.
