import typer
from stock import Stock
from watch_list import Watch_list

app = typer.Typer()

@app.command()
def launch_watchlist() -> Watch_list:
    #NEED to collect the name of watch list to a file
    name = typer.prompt("How would you like to name your watch list?")
    watchlist = Watch_list(name) #creates a watch list object
    typer.echo(f"Created a watch list named {name}.\n")
    typer.echo("""
    COMMANDS FOR WATCH LIST
    1. add-stock
    2. remove-stock
    3. show-stocks
    4. change-name
    """)
    
    while True:
        try:
            command = int(typer.prompt('Enter command number'))
            match command:
                case 1:
                    typer.echo("case 1")
                case 2:
                    typer.echo("case 2")
                case 3:
                    typer.echo("case 3")
                case 4:
                    typer.echo("case 4")
                case _:
                    typer.echo("Command doesn't exist.")
            
        except ValueError:
            typer.echo("Please enter an integer number corresponding to a command.")

if __name__ == "__main__":
    app()