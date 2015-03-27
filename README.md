[whatsapp]: https://www.whatsapp.com/
[ii]: http://tools.suckless.org/ii/

Whatsit is a FIFO based [WhatsApp][whatsapp] client, like [ii][ii].

You send messages by writing to the `in` pipe, and receive messages by
reading from the `out` pipe.

Whatsit expects a client to have both pipes open if it wants to
communicate. If you want to play around with Bash, you will need to open
a separate terminal to communicate with each pipe. In your first
terminal you can run `cat out`, and in another you can run commands like
`echo ... > in`.

[cq]: http://25thandclement.com/~william/projects/cqueues.html

Alternatively, you can run the included `client.lua` script for
interactive use. You need to install [cqueues][cq] to run it.
