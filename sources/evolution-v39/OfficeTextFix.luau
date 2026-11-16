--!strict
-- v43: надписи на экранах мониторов (и ещё ≈190 подписей в картe) были записаны с двойной кодировкой UTF-8: «Б» читалась как «Ð» + управляющий
-- символ. Исправляем на месте: если все символы строки укладываются в диапазон 0..255, это байты исходной UTF-8-строки; результат
-- принимается, только если он корректная UTF-8. Обычный текст (кириллица) не затрагивается.
local function attachTextFix(root: Instance)
	local function repair(text: string): string?
		if not string.find(text, "\195[\128-\191]") then
			return nil
		end
		local parts: {string} = {}
		for _, cp in utf8.codes(text) do
			if cp > 255 then
				return nil
			end
			table.insert(parts, string.char(cp))
		end
		local fixed = table.concat(parts)
		if utf8.len(fixed) and fixed ~= text then
			return fixed
		end
		return nil
	end
	local function fixAll()
		local count = 0
		for _, item in root:GetDescendants() do
			if item:IsA("TextLabel") or item:IsA("TextButton") or item:IsA("TextBox") then
				local ok, fixed = pcall(repair, item.Text)
				if ok and fixed then
					item.Text = fixed
					count += 1
				end
			end
		end
		return count
	end
	fixAll()
	-- метки, добавленные фоновыми апгрейдами позже
	task.delay(20, fixAll)
	task.delay(60, fixAll)
end

return attachTextFix
