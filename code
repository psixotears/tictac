package main

import (
	"fmt"
	"log"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

type Move struct {
	Row, Col int
	Status   string // "new" или "old"
}

var board [3][3]string
var movesX []Move
var movesO []Move
var currentPlayer = "X"
var gameOver = false
var winCells [3][2]int // координаты выигрышной линии

func renderBoard(disableButtons bool) tgbotapi.InlineKeyboardMarkup {
	var rows [][]tgbotapi.InlineKeyboardButton
	for i := 0; i < 3; i++ {
		var row []tgbotapi.InlineKeyboardButton
		for j := 0; j < 3; j++ {
			text := "."
			cell := board[i][j]

			// Подсветка выигрышной линии
			isWinCell := false
			for _, wc := range winCells {
				if wc[0] == i && wc[1] == j {
					isWinCell = true
					break
				}
			}

			if cell != "" {
				switch cell {
				case "X":
					if isWinCell {
						text = "🔴"
					} else {
						text = "❌"
					}
				case "O":
					if isWinCell {
						text = "🔵"
					} else {
						text = "⭕"
					}
				case "x":
					text = "✖️"
				case "o":
					text = "⚪"
				}
			}

			var btn tgbotapi.InlineKeyboardButton
			if disableButtons {
				btn = tgbotapi.NewInlineKeyboardButtonData(text, "disabled")
			} else {
				btn = tgbotapi.NewInlineKeyboardButtonData(text, fmt.Sprintf("%d,%d", i, j))
			}
			row = append(row, btn)
		}
		rows = append(rows, row)
	}

	// Кнопка "Новая игра"
	newGameRow := []tgbotapi.InlineKeyboardButton{
		tgbotapi.NewInlineKeyboardButtonData("🔄 Новая игра", "new_game"),
	}
	rows = append(rows, newGameRow)

	return tgbotapi.NewInlineKeyboardMarkup(rows...)
}

func checkWin(player string) bool {
	// Проверка строк
	for i := 0; i < 3; i++ {
		if board[i][0] == player && board[i][1] == player && board[i][2] == player {
			winCells = [3][2]int{{i, 0}, {i, 1}, {i, 2}}
			return true
		}
	}
	// Проверка столбцов
	for i := 0; i < 3; i++ {
		if board[0][i] == player && board[1][i] == player && board[2][i] == player {
			winCells = [3][2]int{{0, i}, {1, i}, {2, i}}
			return true
		}
	}
	// Диагонали
	if board[0][0] == player && board[1][1] == player && board[2][2] == player {
		winCells = [3][2]int{{0, 0}, {1, 1}, {2, 2}}
		return true
	}
	if board[0][2] == player && board[1][1] == player && board[2][0] == player {
		winCells = [3][2]int{{0, 2}, {1, 1}, {2, 0}}
		return true
	}
	return false
}

func makeMove(player string, row, col int) string {
	if gameOver {
		return "Игра окончена! Нажмите «Новая игра» чтобы начать заново."
	}

	if board[row][col] != "" && board[row][col] != "x" && board[row][col] != "o" {
		return "Неверный ход!"
	}

	if player == "X" {
		board[row][col] = "X"
		movesX = append(movesX, Move{Row: row, Col: col, Status: "new"})
		if len(movesX) > 3 {
			old := movesX[0]
			board[old.Row][old.Col] = "x"
			movesX[0].Status = "old"
			movesX = movesX[1:]
		}
	} else {
		board[row][col] = "O"
		movesO = append(movesO, Move{Row: row, Col: col, Status: "new"})
		if len(movesO) > 3 {
			old := movesO[0]
			board[old.Row][old.Col] = "o"
			movesO[0].Status = "old"
			movesO = movesO[1:]
		}
	}

	if checkWin(player) {
		gameOver = true
		return fmt.Sprintf("🎉 Игрок %s победил! 🎉", player)
	}

	if currentPlayer == "X" {
		currentPlayer = "O"
	} else {
		currentPlayer = "X"
	}

	return fmt.Sprintf("Ход игрока %s", currentPlayer)
}

func resetGame() {
	board = [3][3]string{}
	movesX = []Move{}
	movesO = []Move{}
	currentPlayer = "X"
	gameOver = false
	winCells = [3][2]int{}
}

func main() {
	bot, err := tgbotapi.NewBotAPI("YOUR_TOKEN_HERE")
	if err != nil {
		log.Panic(err)
	}
	bot.Debug = true
	log.Printf("Авторизован как %s", bot.Self.UserName)

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60
	updates := bot.GetUpdatesChan(u)

	for update := range updates {
		if update.Message != nil && update.Message.Text == "/start" {
			resetGame()
			msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Игра началась!\nХод игрока X")
			msg.ReplyMarkup = renderBoard(false)
			bot.Send(msg)
		}

		if update.CallbackQuery != nil {
			data := update.CallbackQuery.Data

			if data == "new_game" {
				resetGame()
				edit := tgbotapi.NewEditMessageTextAndMarkup(
					update.CallbackQuery.Message.Chat.ID,
					update.CallbackQuery.Message.MessageID,
					"Новая игра началась!\nХод игрока X",
					renderBoard(false),
				)
				bot.Send(edit)
				bot.Request(tgbotapi.NewCallback(update.CallbackQuery.ID, ""))
				continue
			}

			var row, col int
			fmt.Sscanf(data, "%d,%d", &row, &col)
			response := makeMove(currentPlayer, row, col)

			edit := tgbotapi.NewEditMessageTextAndMarkup(
				update.CallbackQuery.Message.Chat.ID,
				update.CallbackQuery.Message.MessageID,
				response,
				renderBoard(gameOver),
			)
			bot.Send(edit)
			bot.Request(tgbotapi.NewCallback(update.CallbackQuery.ID, ""))
		}
	}
}
