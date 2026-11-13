from views.tela_login import TelaLogin
from views.app import App


def iniciar_app():
    App().mainloop()


if __name__ == "__main__":
    TelaLogin(ao_logar=iniciar_app).mainloop()