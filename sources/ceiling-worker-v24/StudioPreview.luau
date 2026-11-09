-- Only the disposable QA place gets this manual activation hook.
if game:GetService("RunService"):IsStudio() then
    script:SetAttribute("ForceCeilingInStudio", true)
    local previewSwitch = Instance.new("BindableEvent")
    previewSwitch.Name = "CeilingWorkerLocalQA"
    previewSwitch.Parent = Storage
    previewSwitch.Event:Connect(function(active)
        ceiling:SetActive(active == true)
    end)
end
