# Recompose

Recompose is a flexible Python-based rules engine that supports multiprocessing and asynchronous tasks.

The flexibility comes from the fact that each part of a recompose rule is a function call so every part of a rule can be customized. In addition, rules are written in JSON so they are easy to write and parse.

One major feature of Recompose is allowing for testable conditions. These are conditions that don't have an immediate answer. The most common example of this is an HTTP request. A condition such as "Is this URL a login page?", would involve sending out a request, examining the response, then finally returning an answer of True or False. While it may be the case that this process can be broken down into several primitive condition-action rules, it occurs so often with blackbox testing that this pattern has been integrated into the engine itself.

The second major feature is that the engine can spawn multiple copies of itself and operate in separate threads. The Recompose engine can create numerous copies to send and perform tasks such as collecting URL links, thus forming the basis of a multithreaded crawler.

# Other Features

All methods are added as mixins which favors composition over inheritance. Simply create a class, write the methods, then include the class in the mixin list when the engine is initialized.

Method arguments are handled automatically by the engine. It will search through the stored context data and if the corresponding argument name is found there, it will be used.

Since rules are processed in a top down order, they can be prioritized by simply moving them up or down (because OrderedDict). The reason for a top down order is because rules can be allowed to run more than once. For example, a rule that searches for a keyword in a HTTP response would be run for each new response.

Rules can be grouped in the definition file not just for the purpose of organization, but also for control flow. Take, for example, a group of rules that are ready to run. However, an earlier rule has uncovered a condition that would invalidate the group of rules. Instead of embedding this condition in each rule in the group, it's much cleaner to simply mark the group as completed.

Because rules can be controlled by other rules, it allows for great control over how rules can be executed. Rules can be easily chained so even complicated actions can be broken into multiple rules.
