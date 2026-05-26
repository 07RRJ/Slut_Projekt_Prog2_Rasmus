import bcrypt
from auth.session import SaveSession, ClearSession
import pygame
from ui.elements import Bar, Button
from ui.assets import BASE_WIDTH, BASE_HEIGHT, screen
import sys
import os

clock = pygame.time.Clock()

def GetText(data, text):
    font = pygame.font.Font(None, 36)
    input_box = pygame.Rect(200, 250, 400, 50)
    color_inactive = pygame.Color('gray')
    color_active = pygame.Color('dodgerblue')
    color = color_inactive

    active = False
    text = ""
    while True:
        clock.tick(60)
        screen.fill((30, 30, 30))
        txt_surface = font.render(text, True, (255, 255, 255))

        width = max(400, txt_surface.get_width() + 10)
        input_box.w = width

        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 10))
        pygame.draw.rect(screen, color, input_box, 2)

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = True
                else:
                    active = False

                color = color_active if active else color_inactive

            elif event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:
                    return text
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode

def PromtLogin(data) -> bool:
    selectedIdx = None

    button_rect = (
        pygame.Rect(BASE_WIDTH//2, BASE_HEIGHT//3 + 200 * i, 200, 100) for i in range(3)
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
        screen.fill(data.assets.BLACK[4])

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
                            print("User not found.")
                            return False
                        pw = GetText(data, "Password: ").encode()
                        if bcrypt.checkpw(pw, user["password_hash"].encode()):
                            data.session = {"user_id": user["id"], "username": user["username"]}
                            SaveSession(user["id"], user["username"])
                            print(f"Welcome back, {username}")
                            return True
                        print("Wrong password")
                        return False

                    elif selectedIdx == 1:
                        username = GetText(data, "Choose username: ").strip()
                        pw = GetText(data, "Choose password: ").encode()
                        hashed = bcrypt.hashpw(pw, bcrypt.gensalt()).decode()
                        user = data.db.Register(username, hashed)
                        if user:
                            data.session = {"user_id": user["id"], "username": user["username"]}
                            SaveSession(user["id"], user["username"])
                            print(f"Account created! Welcome, {username}!")
                            return True
                        print("username already taken.")
                        return False
                    else:
                        return

def MainMenu(data): # data.session['username'] - username
    if not data.session:
        if not PromtLogin(data):
            return
    selectedIdx = None

    button_rect = (
        pygame.Rect(BASE_WIDTH//2, BASE_HEIGHT//3 + 200 * i, 200, 100) for i in range(3)
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
        screen.fill(data.assets.BLACK[4])

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