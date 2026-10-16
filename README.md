# Card Wars Linux
A native Linux port in progress of the "Adventure Time: Card Wars" mobile game,
based on [shishkabob27/CardWars](https://github.com/shishkabob27/CardWars).

**Status:** Linux x86-64 build support is implemented. Unity compilation and Steam
Deck gameplay verification are still pending; there is no tested Linux binary yet.

- [Build the native Linux player](docs/LINUX_BUILD.md)
- [Steam Deck installation, controls and testing](docs/STEAM_DECK.md)

The Linux build uses Unity 2017.4.40f1, Mono and desktop OpenGL. It launches directly
on Linux without Proton or Wine. Existing game assets, scenes and save identity
are retained.

Floop the Pig! It's Adventure Time CARD WARS! Play the game inspired by the Adventure TIme episode, 'Card Wars'! Summon creatures and cast spells to battle your way to victory.


CARD COMBAT!

Command an army of awesome warriors, including Husker Knights, Cool Dog the Immortal Maize Walker, and even the Pig to destroy your opponent's forces! Place towers and cast spells to unleash ultimo attacks

CUSTOM DECKS!

Collect new cards to customize your deck for each opponent. Level up your creatures, spells, and towers, or fuse them together to make your cards even more powerful.

HIGH STAKES BATTLES!

Think you've got what it takes to be crowned a Cool Guy, or will you end up drinking from the Dweeb cup? Play as Finn Jake, BMO, Princess Bubblegum, Marceline, Flame Princess and more as you wind your way through the Land of Ooo!

It's CARD WARS! 

## Download

* Linux: [build from source](docs/LINUX_BUILD.md); a verified release is pending.
* [Upstream Windows Version](https://github.com/shishkabob27/CardWars/releases/latest/download/CardWars-Windows.zip)

## Images
![CardWars_r8d9H393Tp](https://i.imgur.com/cXUolY0.jpg)
![CardWars_F7nDRbIxel](https://i.imgur.com/N3BH326.jpg)

## Contributing
Card Wars uses Unity 2017.4.40f1. Linux builds require the matching Linux Build
Support module. See the [build guide](docs/LINUX_BUILD.md) for the scripts,
portability checks and remaining runtime validation.
