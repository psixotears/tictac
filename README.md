package main

import (
	"fmt"
	"log"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

var board [3][3]string
var movesX [][]int
var movesO [][]int
var currentPlayer = "X"

func renderBoard() string {
	result := "  0 1 2\n"
	for i := 0; i < 3; i++ {
		result += fmt.Sprintf("%d ", i)
		for j := 0; j < 3; j++ {
			if board[i][j] == "" {
				result += "."
			} else {
				result += board[i][j]
			}
			if j < 2 {
				result += " "
			}
		}
		result += "\n"
	}
	return result
}

func checkWin(player string) bool {
	// строки и столбцы
	for i := 0; i < 3; i++ {
		if board[i][0] == player && board[i][1] == player && board[i][2] == player {
			return true
		}
		if board[0][i] == player && board[1][i] == player && board[2][i] == player {
			return true
		}
	}
	// диагонали
	if board[0][0] == player && board[1][1] == player && board[2][2] == player {
		return true
	}
	if board[0][2] == player && board[1][1] == player && board[2][0] == player {
		return true
	}
	return false
}

func makeMove(player string, row, col int) string {
	if row < 0 || row > 2 || col < 0 || col > 2 || board[row][col] != "" {
		return "Неверный ход!"
	}

	board[row][col] = player

	if player == "X" {
		movesX = append(movesX, []int{row, col})
		if len(movesX) > 3 {
			old := movesX[0]
			board[old[0]][old[1]] = ""
			movesX = movesX[1:]
		}
	} else {
		movesO = append(movesO, []int{row, col})
		if len(movesO) > 3 {
			old := movesO[0]
			board[old[0]][old[1]] = ""
			movesO = movesO[1:]
		}
	}

	if checkWin(player) {
		return fmt.Sprintf("Игрок %s победил!\n%s", player, renderBoard())
	}

	// смена игрока
	if currentPlayer == "X" {
		currentPlayer = "O"
	} else {
		currentPlayer = "X"
	}
	return fmt.Sprintf("%s\nХод игрока %s", renderBoard(), currentPlayer)
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
		if update.Message != nil {
			switch update.Message.Text {
			case "/start":
				board = [3][3]string{}
				movesX = [][]int{}
				movesO = [][]int{}
				currentPlayer = "X"
				msg := tgbotapi.NewMessage(update.Message.Chat.ID,
					"Игра началась!\n"+renderBoard()+"\nХод игрока X")
				bot.Send(msg)
			default:
				var r, c int
				_, err := fmt.Sscanf(update.Message.Text, "%d %d", &r, &c)
				if err != nil {
					msg := tgbotapi.NewMessage(update.Message.Chat.ID, "Введите ход в формате: `строка столбец` (например: 1 2)")
					bot.Send(msg)
					continue
				}
				response := makeMove(currentPlayer, r, c)
				msg := tgbotapi.NewMessage(update.Message.Chat.ID, response)
				bot.Send(msg)
			}
		}
	}
}

