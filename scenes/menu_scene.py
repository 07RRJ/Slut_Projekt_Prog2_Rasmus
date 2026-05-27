import bcrypt
from auth.session import SaveSession, ClearSession
import pygame
from ui.elements import Bar
from ui.button import Button
from ui.assets import BASE_WIDTH, BASE_HEIGHT, screen
import sys
import os

clock = pygame.time.Clock()

def GetText(data, text, password=False) -> str:
    text = data.assets.text_font.render(text, True, data.assets.BLACK[5])

    input_box = pygame.Rect(BASE_WIDTH//2-200, BASE_HEIGHT//2-25, 400, 50)
    color = data.assets.BLACK[2]
    active = False
    text_input = ""

    if password:
        txt_surface = data.assets.text_font.render(f"{"*"*len(text_input)}", True, data.assets.BLACK[5])
    else:
        txt_surface = data.assets.text_font.render(text_input.upper(), True, data.assets.BLACK[5])

    while True:
        clock.tick(60)
        pygame.draw.rect(screen, data.assets.BLACK[3], data.assets.MENU)

        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 10))
        pygame.draw.rect(screen, color, input_box, 2)
        screen.blit(text, (input_box.x+5, input_box.y-50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = True
                else:
                    active = False

                color = data.assets.BLUE[0] if active else data.assets.BLACK[2]

            elif event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:
                    return str(text_input)
                elif event.key == pygame.K_BACKSPACE:
                    text_input = text_input[:-1]
                else:
                    text_input += event.unicode

                if password:
                    txt_surface = data.assets.text_font.render(f"{"*"*len(text_input)}", True, data.assets.BLACK[5])
                else:
                    txt_surface = data.assets.text_font.render(text_input.upper(), True, data.assets.BLACK[5])

                width = max(400, txt_surface.get_width() + 10)
                input_box.w = width

def PromtLogin(data) -> bool:
    selectedIdx = None

    button_rect = (
        pygame.Rect(
            BASE_WIDTH//3 + 200 + 300 * i, 
            BASE_HEIGHT - 200,
            200, 
            100
        ) for i in range(3)
    )

    button_text = ("Login", "Register", "Back")

    buttons = []
    for idx, rect in enumerate(button_rect):
        buttons.append(
            Button(
                Text=f"{button_text[idx]}",
                Rect=rect,
                Font=data.assets.text_font,
                Colour=data.assets.BLACK[0]
            )
        )

    while True:
        clock.tick(60)
        screen.blit(data.assets.MAIN_MENU, (0, 0))

        for idx, btn in enumerate(buttons):
            btn.draw(idx == selectedIdx)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            pos = pygame.mouse.get_pos()
            selectedIdx = None
            for idx, btn in enumerate(buttons):
                if btn.rect.collidepoint(pos):
                    selectedIdx = idx
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if selectedIdx is not None:
                    if selectedIdx == 0:
                        username = GetText(data, "Username: ").strip()
                        user = data.db.Login(username)
                        if not user:
                            return False
                        pw = GetText(data, "Password: ", True).encode()
                        if bcrypt.checkpw(pw, user["password_hash"].encode()):
                            data.session = {"user_id": user["id"], "username": user["username"]}
                            SaveSession(user["id"], user["username"])
                            return True
                        return False

                    elif selectedIdx == 1:
                        username = GetText(data, "Choose username: ").strip()
                        pw = GetText(data, "Choose password: ", True).encode()
                        hashed = bcrypt.hashpw(pw, bcrypt.gensalt()).decode()
                        user = data.db.Register(username, hashed)
                        if user:
                            data.session = {"user_id": user["id"], "username": user["username"]}
                            SaveSession(user["id"], user["username"])
                            return True
                        return False
                    else:
                        return None

def MainMenu(data):
    if not data.session:
        login = PromtLogin(data)
        if login is None:
            return
        elif not login:
            MainMenu(data)
    selectedIdx = None

    user = data.assets.title_font.render(
        data.session['username'], 
        True, 
        data.assets.RED[2]
    )

    button_rect = (
        pygame.Rect(
            BASE_WIDTH//3 + 200 + 300 * i, 
            BASE_HEIGHT - 200,
            200, 
            100
        ) for i in range(3)
    )

    button_text = ("find game", "log out", "quit")

    buttons = []
    for idx, rect in enumerate(button_rect):
        buttons.append(
            Button(
                Text=f"{button_text[idx]}",
                Rect=rect,
                Font=data.assets.text_font,
                Colour=data.assets.BLACK[0]
            )
        )

    while True:
        clock.tick(60)
        screen.blit(data.assets.MAIN_MENU, (0, 0))
        screen.blit(user, (32, 32))

        for idx, btn in enumerate(buttons):
            btn.draw(idx == selectedIdx)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            pos = pygame.mouse.get_pos()
            selectedIdx = None
            for idx, btn in enumerate(buttons):
                if btn.rect.collidepoint(pos):
                    selectedIdx = idx
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if selectedIdx is not None:

                    if selectedIdx == 0:
                        from logic.match_making import FindGame
                        FindGame(data)
                    elif selectedIdx == 1:
                        ClearSession()
                        data.session = None
                        MainMenu(data)
                    else:
                        return False